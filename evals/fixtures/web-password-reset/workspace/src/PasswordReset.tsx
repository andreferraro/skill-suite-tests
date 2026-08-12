import { FormEvent, useRef, useState } from "react";

export type ResetClient = (email: string) => Promise<string>;

type Result =
  | { kind: "idle"; message: "" }
  | { kind: "success" | "error"; message: string };

export function PasswordReset({ requestReset }: { requestReset: ResetClient }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result>({ kind: "idle", message: "" });
  const latestRequest = useRef(0);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const requestId = latestRequest.current + 1;
    latestRequest.current = requestId;
    setLoading(true);
    setResult({ kind: "idle", message: "" });

    try {
      const message = await requestReset(email);
      if (requestId !== latestRequest.current) return;
      setResult({ kind: "success", message });
    } catch (error) {
      if (requestId !== latestRequest.current) return;
      setResult({
        kind: "error",
        message: error instanceof Error ? error.message : "Falha ao solicitar recuperação",
      });
    } finally {
      if (requestId === latestRequest.current) setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} aria-label="Recuperação de senha">
      <label htmlFor="email">E-mail</label>
      <input
        id="email"
        name="email"
        type="email"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <button type="submit" disabled={loading}>
        {loading ? "Enviando..." : "Enviar link"}
      </button>
      {result.kind !== "idle" ? (
        <p role={result.kind === "error" ? "alert" : "status"}>{result.message}</p>
      ) : null}
    </form>
  );
}
