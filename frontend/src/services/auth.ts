export type Role = "USUARIO" | "OPERADOR" | "ADMIN" | "AUDITOR";

export interface User {
  id: string;
  full_name: string;
  role: Role;
  contact_verified: boolean;
}

export interface Session {
  user: User;
  expires_at: string;
}

export interface Login {
  email: string;
  password: string;
}

export interface Register extends Login {
  full_name: string;
  phone?: string;
}

interface Resource {
  id: string;
  state?: string;
}

interface ErrorBody {
  code?: unknown;
  message?: unknown;
  correlation_id?: unknown;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly correlationId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch("/api/v1/auth" + path, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "SIN_CONEXION", "No se pudo conectar con BUZON Xpress.");
  }
  if (!response.ok) {
    const data: ErrorBody | null = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      typeof data?.code === "string" ? data.code : "PETICION_RECHAZADA",
      typeof data?.message === "string" ? data.message : "No se pudo completar la solicitud.",
      typeof data?.correlation_id === "string"
        ? data.correlation_id
        : response.headers.get("X-Correlation-ID") ?? undefined,
    );
  }
  return (await response.json()) as T;
}

async function mutate<T>(path: string, body?: object): Promise<T> {
  const { csrf_token } = await request<{ csrf_token: string }>("/csrf");
  const headers: Record<string, string> = { "X-CSRF-Token": csrf_token };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  return request<T>(path, { method: "POST", headers, body: JSON.stringify(body) });
}

export const auth = {
  register: (body: Register) => mutate<User>("/register", body),
  login: (body: Login) => mutate<Session>("/login", body),
  me: () => request<User>("/me"),
  logout: () => mutate<Resource>("/logout"),
  verifyContact: (token: string) => mutate<Resource>("/verify-contact", { token }),
};
