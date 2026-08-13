import { useEffect } from "react";
import { render } from "vitest-browser-react";
import { usePapaParse } from "./usePapaParse";

type ImporterState = ReturnType<typeof usePapaParse<{ id: number }>>["importer"];

type ParseOptions<T> = {
  complete(results: { data: T[]; errors: { message: string }[] }): Promise<void>;
  error(error: Error): void;
};

const parseMock = vi.fn();

vi.mock("papaparse", () => ({
  parse: (...args: unknown[]) => parseMock(...args),
}));

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function Harness({
  batchSize,
  processBatch,
  onState,
}: {
  batchSize: number;
  processBatch: (rows: Array<{ id: number }>) => Promise<void>;
  onState: (state: ImporterState) => void;
}) {
  const { importer, parseCsv, reset } = usePapaParse<{ id: number }>({
    batchSize,
    processBatch,
  });

  useEffect(() => {
    onState(importer);
  }, [importer, onState]);

  return (
    <div>
      <button
        type="button"
        onClick={() => parseCsv(new File(["id\n1"], "contacts.csv", { type: "text/csv" }))}
      >
        parse
      </button>
      <button type="button" onClick={reset}>
        reset
      </button>
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

  it("tracks parsing, running progress and completion", async () => {
    vi.spyOn(Date, "now")
      .mockReturnValueOnce(1000)
      .mockReturnValueOnce(1010)
      .mockReturnValueOnce(2000)
      .mockReturnValueOnce(2020);

    const states: ImporterState[] = [];
    const batches: Array<{ promise: Promise<void>; resolve: () => void }> = [];
    const processBatch = vi.fn(() => {
      const deferred = createDeferred<void>();
      batches.push({ promise: deferred.promise, resolve: () => deferred.resolve() });
      return deferred.promise;
    });

    const screen = await render(
      <Harness batchSize={2} processBatch={processBatch} onState={(state) => states.push(state)} />,
    );
    await screen.getByRole("button", { name: "parse" }).click();

    await expect.poll(() => parseMock.mock.calls.length).toBe(1);
    await expect.poll(() => states.at(-1)?.state).toBe("parsing");

    const options = parseMock.mock.calls[0][1] as ParseOptions<{ id: number }>;
    const completion = options.complete({
      data: [{ id: 1 }, { id: 2 }, { id: 3 }],
      errors: [],
    });

    await expect.poll(() => states.at(-1)).toMatchObject({
      state: "running",
      rowCount: 3,
      importCount: 0,
      errorCount: 0,
      remainingTime: null,
    });

    batches[0].resolve();
    await batches[0].promise;
    await expect.poll(() => states.at(-1)).toMatchObject({
      state: "running",
      importCount: 2,
      errorCount: 0,
      remainingTime: 5,
    });

    batches[1].resolve();
    await batches[1].promise;
    await completion;
    await expect.poll(() => states.at(-1)).toMatchObject({
      state: "complete",
      importCount: 3,
      errorCount: 0,
      remainingTime: null,
    });
  });

  it("increments errorCount on failed batch and continues", async () => {
    const states: ImporterState[] = [];
    const batches: Array<{ promise: Promise<void>; resolve: () => void; reject: () => void }> = [];
    const processBatch = vi.fn(() => {
      const deferred = createDeferred<void>();
      batches.push({
        promise: deferred.promise,
        resolve: () => deferred.resolve(),
        reject: () => deferred.reject(new Error("batch failed")),
      });
      return deferred.promise;
    });

    const screen = await render(
      <Harness batchSize={2} processBatch={processBatch} onState={(state) => states.push(state)} />,
    );
    await screen.getByRole("button", { name: "parse" }).click();
    await expect.poll(() => parseMock.mock.calls.length).toBe(1);

    const options = parseMock.mock.calls[0][1] as ParseOptions<{ id: number }>;
    const completion = options.complete({
      data: [{ id: 1 }, { id: 2 }, { id: 3 }],
      errors: [{ message: "warning" }],
    });

    batches[0].reject();
    await Promise.resolve();
    await expect.poll(() => states.at(-1)).toMatchObject({
      state: "running",
      importCount: 0,
      errorCount: 3,
    });

    batches[1].resolve();
    await batches[1].promise;
    await completion;
    await expect.poll(() => states.at(-1)).toMatchObject({
      state: "complete",
      importCount: 1,
      errorCount: 3,
    });
  });

  it("moves to error state on parser fatal error", async () => {
    const states: ImporterState[] = [];
    const screen = await render(
      <Harness
        batchSize={2}
        processBatch={vi.fn().mockResolvedValue(undefined)}
        onState={(state) => states.push(state)}
      />,
    );
    await screen.getByRole("button", { name: "parse" }).click();
    await expect.poll(() => parseMock.mock.calls.length).toBe(1);

    const options = parseMock.mock.calls[0][1] as ParseOptions<{ id: number }>;
    options.error(new Error("invalid csv stream"));

    await expect.poll(() => states.at(-1)).toMatchObject({
      state: "error",
      error: { message: "invalid csv stream" },
    });
  });

  it("ignores stale complete callback after reset during parsing", async () => {
    const states: ImporterState[] = [];
    const processBatch = vi.fn().mockResolvedValue(undefined);
    const screen = await render(
      <Harness batchSize={2} processBatch={processBatch} onState={(state) => states.push(state)} />,
    );
    await screen.getByRole("button", { name: "parse" }).click();
    await expect.poll(() => parseMock.mock.calls.length).toBe(1);
    await screen.getByRole("button", { name: "reset" }).click();
    const resetSnapshotIndex = states.length;

    const options = parseMock.mock.calls[0][1] as ParseOptions<{ id: number }>;
    await options.complete({
      data: [{ id: 1 }, { id: 2 }],
      errors: [],
    });

    await expect.poll(() => states.at(-1)?.state).toBe("idle");
    expect(processBatch).not.toHaveBeenCalled();
    expect(states.slice(resetSnapshotIndex).map((state) => state.state)).not.toContain(
      "running",
    );
  });

  it("keeps idle after reset while pending batch resolves", async () => {
    const states: ImporterState[] = [];
    const firstBatch = createDeferred<void>();
    const processBatch = vi
      .fn()
      .mockReturnValueOnce(firstBatch.promise)
      .mockResolvedValueOnce(undefined);
    const screen = await render(
      <Harness batchSize={2} processBatch={processBatch} onState={(state) => states.push(state)} />,
    );
    await screen.getByRole("button", { name: "parse" }).click();
    await expect.poll(() => parseMock.mock.calls.length).toBe(1);

    const options = parseMock.mock.calls[0][1] as ParseOptions<{ id: number }>;
    const completion = options.complete({
      data: [{ id: 1 }, { id: 2 }, { id: 3 }],
      errors: [],
    });

    await expect.poll(() => states.at(-1)?.state).toBe("running");
    await screen.getByRole("button", { name: "reset" }).click();
    await expect.poll(() => states.at(-1)?.state).toBe("idle");

    firstBatch.resolve();
    await firstBatch.promise;
    await completion;
    await expect.poll(() => states.at(-1)?.state).toBe("idle");
    expect(processBatch).toHaveBeenCalledTimes(1);
  });
});
