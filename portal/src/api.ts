import type { Theme } from "./theme";
import type { Channel, SkillDetail, SkillSummary, User, VersionDetail } from "./types";

/** Erro devolvido pela API no formato { code, message }. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

let onUnauthorized: (() => void) | null = null;

/** Chamado quando uma rota protegida responde 401 (sessão expirada ou ausente). */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, init);
  } catch {
    throw new ApiError("network_error", "Não foi possível falar com o hub. Ele está no ar?", 0);
  }
  if (!response.ok) {
    let code = "http_error";
    let message = `Erro ${response.status} ao falar com o hub.`;
    try {
      const body = (await response.json()) as { code?: string; message?: string };
      code = body.code ?? code;
      message = body.message ?? message;
    } catch {
      // resposta sem JSON: mantém a mensagem genérica
    }
    if (response.status === 401 && !path.startsWith("/auth/login")) onUnauthorized?.();
    throw new ApiError(code, message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const enc = encodeURIComponent;

export const listSkills = () => request<SkillSummary[]>("/skills");

export const getSkill = (name: string) => request<SkillDetail>(`/skills/${enc(name)}`);

export const getVersion = (name: string, version: string) =>
  request<VersionDetail>(`/skills/${enc(name)}/versions/${enc(version)}`);

export function uploadSkill(file: File, version: string) {
  const body = new FormData();
  body.append("file", file);
  body.append("version", version);
  return request<VersionDetail>("/skills/upload", { method: "POST", body });
}

export const promote = (name: string, version: string, to: Channel) =>
  request<VersionDetail>(`/skills/${enc(name)}/versions/${enc(version)}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to }),
  });

export const deprecate = (name: string, version: string) =>
  request<VersionDetail>(`/skills/${enc(name)}/versions/${enc(version)}/deprecate`, {
    method: "POST",
  });

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const login = (username: string, password: string) =>
  request<User>("/auth/login", json("POST", { username, password }));

export const logout = () => request<void>("/auth/logout", { method: "POST" });

export const me = () => request<User>("/auth/me");

export const saveTheme = (theme: Theme) => request<User>("/auth/theme", json("PUT", { theme }));
