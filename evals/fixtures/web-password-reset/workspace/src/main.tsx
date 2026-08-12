import { createRoot } from "react-dom/client";

import { PasswordReset } from "./PasswordReset";


async function requestReset(email: string): Promise<string> {
  const response = await fetch("/api/password-reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const payload = (await response.json()) as { message?: string };
  if (!response.ok) {
    throw new Error(payload.message ?? "Falha ao solicitar recuperação");
  }
  return payload.message ?? "Link enviado";
}

const root = document.getElementById("root");
if (!root) throw new Error("root element is missing");
createRoot(root).render(<PasswordReset requestReset={requestReset} />);
