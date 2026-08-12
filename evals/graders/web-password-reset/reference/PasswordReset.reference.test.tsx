import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PasswordReset } from "../../src/PasswordReset";

afterEach(cleanup);

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("PasswordReset reference behavior", () => {
  it("disables submit while the request is pending", async () => {
    const pending = deferred<string>();
    render(<PasswordReset requestReset={() => pending.promise} />);
    const user = userEvent.setup();
    await user.type(screen.getByRole("textbox", { name: "E-mail" }), "user@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar link" }));
    expect(screen.getByRole("button", { name: "Enviando..." })).toBeDisabled();
    pending.resolve("Enviado");
    await screen.findByRole("status");
  });

  it("announces request errors", async () => {
    render(<PasswordReset requestReset={() => Promise.reject(new Error("Serviço indisponível"))} />);
    const user = userEvent.setup();
    await user.type(screen.getByRole("textbox", { name: "E-mail" }), "user@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar link" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Serviço indisponível");
  });

  it("supports labeled keyboard input and submit", async () => {
    const requestReset = vi.fn().mockResolvedValue("Enviado");
    render(<PasswordReset requestReset={requestReset} />);
    const user = userEvent.setup();
    await user.tab();
    expect(screen.getByRole("textbox", { name: "E-mail" })).toHaveFocus();
    await user.type(screen.getByRole("textbox", { name: "E-mail" }), "user@example.com");
    await user.tab();
    await user.keyboard("{Enter}");
    await waitFor(() => expect(requestReset).toHaveBeenCalledWith("user@example.com"));
  });

  it("ignores a stale response after a newer request", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const requestReset = vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    render(<PasswordReset requestReset={requestReset} />);
    const user = userEvent.setup();
    const input = screen.getByRole("textbox", { name: "E-mail" });
    await user.type(input, "first@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar link" }));
    await user.clear(input);
    await user.type(input, "second@example.com");
    fireEvent.submit(screen.getByRole("form", { name: "Recuperação de senha" }));
    await act(async () => second.resolve("Resposta nova"));
    expect(await screen.findByText("Resposta nova")).toBeVisible();
    await act(async () => first.resolve("Resposta antiga"));
    expect(screen.queryByText("Resposta antiga")).not.toBeInTheDocument();
  });
});
