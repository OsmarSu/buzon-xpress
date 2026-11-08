interface ErrorBody {
  code?: unknown;
  message?: unknown;
  correlation_id?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly correlationId?: string;

  constructor(status: number, code: string, message: string, correlationId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
  }
}

export function describeError(error: unknown): string {
  if (!(error instanceof ApiError)) return "Ocurrió un problema al procesar la respuesta.";
  return error.correlationId ? error.message + " Referencia: " + error.correlationId : error.message;
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch("/api/v1" + path, { ...init, credentials: "same-origin", cache: "no-store" });
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
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(0, "RESPUESTA_INVALIDA", "No se pudo confirmar la respuesta del servidor.",
      response.headers.get("X-Correlation-ID") ?? undefined);
  }
}

type Method = "POST" | "PUT" | "PATCH";

export async function mutate<T>(path: string, body?: object, options?: {
  method?: Method;
  key?: string;
}): Promise<T> {
  const { csrf_token } = await request<{ csrf_token: string }>("/auth/csrf");
  const headers: Record<string, string> = { "X-CSRF-Token": csrf_token };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (options?.key) headers["Idempotency-Key"] = options.key;
  return request<T>(path, { method: options?.method ?? "POST", headers, body: JSON.stringify(body) });
}

export function mutationSeries() {
  let pending: { path: string; method: Method; data: string; key: string } | undefined;
  return async function send<T>(path: string, body: object, method: Method = "POST"): Promise<T> {
    const data = JSON.stringify(body);
    if (pending?.path !== path || pending?.method !== method || pending?.data !== data) {
      pending = { path, method, data, key: crypto.randomUUID() };
    }
    const current = pending;
    try {
      const result = await mutate<T>(path, body, current);
      if (pending === current) pending = undefined;
      return result;
    } catch (error) {
      // A confirmed rejection ends the attempt. Ambiguous responses keep the key.
      if (pending === current && error instanceof ApiError && error.status >= 400 && error.status < 500
        && error.status !== 408 && error.status !== 425 && error.status !== 409) {
        pending = undefined;
      }
      throw error;
    }
  };
}
