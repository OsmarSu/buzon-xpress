import type { Credential, Custody, MobileSession, MfaChallenge, Notice, Point, Quote, Resource, Size, Tracking, User } from "./types";

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) { super(message); this.status = status; this.code = code; }
}
type Fetcher = (url: string, init?: RequestInit) => Promise<Response>;
export interface ClientOptions { baseUrl: string; fetcher: Fetcher; uuid: () => string; onUnauthorized?: () => void }

export class BuzonClient {
  private token: string | null = null;
  private options: ClientOptions;
  constructor(options: ClientOptions) { this.options = options; }
  setUnauthorizedHandler(handler?: () => void) { this.options.onUnauthorized = handler; }
  setToken(token: string | null) { this.token = token; }
  async request<T>(path: string, method = "GET", body?: object, authorized = true, key?: string): Promise<T> {
    if (authorized && !this.token) throw new ApiError(401, "ACCESO_REQUERIDO", "Inicia sesión para continuar.");
    const requestToken = this.token;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 40000);
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (authorized) headers.Authorization = "Bearer " + this.token;
    if (key) headers["Idempotency-Key"] = key;
    let response: Response;
    try {
      response = await this.options.fetcher(this.options.baseUrl.replace(/\/$/, "") + "/api/v1" + path, {
        method, headers, credentials: "omit", cache: "no-store", signal: controller.signal,
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      });
    } catch {
      clearTimeout(timer);
      throw new ApiError(0, "SIN_CONEXION", "No se pudo conectar. Comprueba tu conexión y vuelve a intentarlo.");
    }
    let data: any;
    try { data = await response.json(); }
    catch { throw new ApiError(0, "RESPUESTA_INCIERTA", "No se pudo confirmar la respuesta. Consulta el estado antes de repetir la operación."); }
    finally { clearTimeout(timer); }
    if (data === null || typeof data !== "object") throw new ApiError(0, "RESPUESTA_INCIERTA", "No se pudo confirmar la respuesta. Consulta el estado antes de repetir la operación.");
    if (!response.ok) {
      if (authorized && response.status === 401 && this.token === requestToken) {
        this.token = null;
        this.options.onUnauthorized?.();
      }
      throw new ApiError(response.status, typeof data.code === "string" ? data.code : "SOLICITUD_RECHAZADA",
        typeof data.message === "string" ? data.message : "No se pudo completar la solicitud.");
    }
    return data as T;
  }
  mutation() {
    let pending: { signature: string; key: string } | undefined;
    return async <T>(path: string, body: object): Promise<T> => {
      const signature = path + JSON.stringify(body);
      if (!pending || pending.signature !== signature) pending = { signature, key: this.options.uuid() };
      const current = pending;
      try {
        const result = await this.request<T>(path, "POST", body, true, current.key);
        if (pending === current) pending = undefined;
        return result;
      } catch (error) {
        if (pending === current && error instanceof ApiError && error.status >= 400 && error.status < 500
          && ![408, 409, 425].includes(error.status)) pending = undefined;
        throw error;
      }
    };
  }
  login = (email: string, password: string) => this.request<MobileSession | MfaChallenge>("/mobile/auth/login", "POST", { email, password }, false);
  verifyMfa = (challenge_token: string, code: string) => this.request<MobileSession>("/mobile/auth/mfa/verify", "POST", { challenge_token, code }, false);
  register = (body: { email: string; password: string; full_name: string; phone?: string }) => this.request<User>("/mobile/auth/register", "POST", body, false);
  requestReset = (email: string) => this.request<Resource>("/mobile/auth/password-reset/request", "POST", { email }, false);
  logout = () => this.request<Resource>("/mobile/auth/logout", "POST", {});
  me = () => this.request<User>("/auth/me");
  points = () => this.request<Point[]>("/points", "GET", undefined, false);
  quote = (point: string, size: Size, hours: number) => this.request<Quote>("/points/" + encodeURIComponent(point) + "/quote?"
    + new URLSearchParams({ size_category: size, duration_hours: String(hours) }), "GET", undefined, false);
  list = (state = "") => this.request<Custody[]>("/custodies" + (state ? "?state=" + encodeURIComponent(state) : ""));
  detail = (id: string) => this.request<Custody>("/custodies/" + encodeURIComponent(id));
  tracking = (reference: string) => this.request<Tracking>("/public-tracking/" + encodeURIComponent(reference), "GET", undefined, false);
  notices = () => this.request<Notice[]>("/notifications");
  readNotice = (id: string) => this.request<Resource>("/notifications/" + encodeURIComponent(id) + "/read", "POST", {});
  issue = (id: string, reissue: boolean) => this.request<Credential>("/custodies/" + encodeURIComponent(id) + "/credentials", "POST", { reissue });
  rotate = (id: string) => this.request<{ public_reference: string }>("/custodies/" + encodeURIComponent(id) + "/public-reference", "POST", {});
  security = () => this.request<{ enabled: boolean; recovery_codes_remaining: number }>("/auth/mfa");
}
