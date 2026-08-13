import { useEffect } from "react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render } from "vitest-browser-react";
import { usePapaParse } from "./usePapaParse";

const { parseMock } = vi.hoisted(() => ({
  parseMock: vi.fn(),
}));

vi.mock("papaparse", () => ({
  parse: parseMock,
}));

type ParseOptions<T> = {
  complete(results: { data: T[]; errors: unknown[] }): void | Promise<void>;
  error(error: Error): void;
};

type Deferred<T> = {
  promise: Promise<T>;
  resolve(value: T): void;
  reject(reason?: unknown): void;
};

const createDeferred = <T,>(): Deferred<T> => {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
};

function HookHarness<T>({
  batchSize,
  processBatch,
  onImporterChange,
}: {
  batchSize: number;
  processBatch(batch: T[]): Promise<void>;
  onImporterChange(value: ReturnType<typeof usePapaParse<T>>["importer"]): void;
}) {
  const { importer, parseCsv, reset } = usePapaParse<T>({
    batchSize,
    processBatch,
  });

  useEffect(() => {
    onImporterChange(importer);
  }, [importer, onImporterChange]);

  return (
    <div>
      <button
        onClick={() =>
          parseCsv(new File(["name\nAda"], "contacts.csv", { type: "text/csv" }))
        }
      >
        parse
      </button>
      <button onClick={reset}>reset</button>
    </div>
  );
}

describe("usePapaParse", () => {
  beforeEach(() => {
    parseMock.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("tracks parsing, batching progress and completion", async () => {
    const nowValues = [1000, 1010, 1010, 1030];
    let nowIndex = 0;
    vi.spyOn(Date, "now").mockImplementation(() => nowValues[nowIndex++] ?? 1030);

    const firstBatch = createDeferred<void>();
    const secondBatch = createDeferred<void>();
    const processBatch = vi
      .fn<(batch: Array<{ name: string }>) => Promise<void>>()
      .mockImplementationOnce(() => firstBatch.promise)
      .mockImplementationOnce(() => secondBatch.promise);

    const importerStates: Array<ReturnType<typeof usePapaParse>["importer"]> = [];
    const screen = await render(
      <HookHarness<{ name: string }>
        batchSize={2}
        processBatch={processBatch}
        onImporterChange={(state) => importerStates.push(state)}
      />,
    );

    await screen.getByRole("button", { name: "parse" }).click();

    expect(importerStates.at(-1)).toEqual({ state: "parsing" });
    expect(parseMock).toHaveBeenCalledTimes(1);

    const options = parseMock.mock.calls[0][1] as ParseOptions<{ name: string }>;
    void options.complete({
      data: [{ name: "Ada" }, { name: "Grace" }, { name: "Linus" }],
      errors: [{}],
    });

    expect(processBatch).toHaveBeenNthCalledWith(1, [
      { name: "Ada" },
      { name: "Grace" },
    ]);

    firstBatch.resolve();
    await expect
      .poll(() => {
        const latest = importerStates.at(-1);
        if (!latest || latest.state !== "running") {
          return null;
        }
        return {
          importCount: latest.importCount,
          rowCount: latest.rowCount,
          errorCount: latest.errorCount,
          hasRemainingTime: latest.remainingTime !== null,
        };
      })
      .toEqual({
        importCount: 2,
        rowCount: 3,
        errorCount: 1,
        hasRemainingTime: true,
      });

    expect(processBatch).toHaveBeenNthCalledWith(2, [{ name: "Linus" }]);

    secondBatch.resolve();
    await expect.poll(() => importerStates.at(-1)).toEqual({
      state: "complete",
      importCount: 3,
      rowCount: 3,
      errorCount: 1,
      remainingTime: null,
    });
  });

  it("adds batch size to errorCount when processBatch fails and then continues", async () => {
    const firstBatch = createDeferred<void>();
    const secondBatch = createDeferred<void>();
    const processBatch = vi
      .fn<(batch: Array<{ name: string }>) => Promise<void>>()
      .mockImplementationOnce(() => firstBatch.promise)
      .mockImplementationOnce(() => secondBatch.promise);
    vi.spyOn(console, "error").mockImplementation(() => {});

    const importerStates: Array<ReturnType<typeof usePapaParse>["importer"]> = [];
    const screen = await render(
      <HookHarness<{ name: string }>
        batchSize={2}
        processBatch={processBatch}
        onImporterChange={(state) => importerStates.push(state)}
      />,
    );

    await screen.getByRole("button", { name: "parse" }).click();
    const options = parseMock.mock.calls[0][1] as ParseOptions<{ name: string }>;
    void options.complete({
      data: [{ name: "A" }, { name: "B" }, { name: "C" }, { name: "D" }],
      errors: [],
    });

    firstBatch.reject(new Error("batch failed"));
    await expect
      .poll(() => {
        const latest = importerStates.at(-1);
        if (!latest || latest.state !== "running") {
          return null;
        }
        return latest.errorCount;
      })
      .toBe(2);

    secondBatch.resolve();
    await expect.poll(() => importerStates.at(-1)).toEqual({
      state: "complete",
      importCount: 2,
      rowCount: 4,
      errorCount: 2,
      remainingTime: null,
    });
  });

  it("moves to error state when papaparse fails", async () => {
    const processBatch = vi.fn<(batch: Array<{ name: string }>) => Promise<void>>();
    vi.spyOn(console, "error").mockImplementation(() => {});
    const importerStates: Array<ReturnType<typeof usePapaParse>["importer"]> = [];

    const screen = await render(
      <HookHarness<{ name: string }>
        batchSize={2}
        processBatch={processBatch}
        onImporterChange={(state) => importerStates.push(state)}
      />,
    );

    await screen.getByRole("button", { name: "parse" }).click();
    const options = parseMock.mock.calls[0][1] as ParseOptions<{ name: string }>;
    const parseError = new Error("invalid csv");

    options.error(parseError);

    await expect.poll(() => importerStates.at(-1)).toEqual({
      state: "error",
      error: parseError,
    });
    expect(processBatch).not.toHaveBeenCalled();
  });

  it("cancels an in-flight import when reset is called", async () => {
    const batch = createDeferred<void>();
    const processBatch = vi
      .fn<(batch: Array<{ name: string }>) => Promise<void>>()
      .mockImplementationOnce(() => batch.promise);

    const importerStates: Array<ReturnType<typeof usePapaParse>["importer"]> = [];
    const screen = await render(
      <HookHarness<{ name: string }>
        batchSize={5}
        processBatch={processBatch}
        onImporterChange={(state) => importerStates.push(state)}
      />,
    );

    await screen.getByRole("button", { name: "parse" }).click();
    const options = parseMock.mock.calls[0][1] as ParseOptions<{ name: string }>;
    void options.complete({
      data: [{ name: "Ada" }],
      errors: [],
    });

    await expect.poll(() => importerStates.at(-1)?.state).toBe("running");

    await screen.getByRole("button", { name: "reset" }).click();
    await expect.poll(() => importerStates.at(-1)).toEqual({ state: "idle" });

    batch.resolve();
    await Promise.resolve();
    await expect.poll(() => importerStates.at(-1)).toEqual({ state: "idle" });
  });
});
