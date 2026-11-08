import { mutate, request } from "./api";
import type { Resource } from "./auth";

export const sizes = ["PEQUENO", "MEDIANO", "GRANDE"] as const;
export type Size = (typeof sizes)[number];
export type CustodyState =
  | "REGISTRADA" | "EN_CUSTODIA" | "RETIRO_EN_CURSO" | "RETIRADA"
  | "DEVOLUCION_EN_CURSO" | "DEVUELTA" | "CANCELADA";
export interface Point {
  id: string;
  name: string;
  address: string;
  opening_hours: Record<string, unknown>;
  is_active: boolean;
}

export interface Custody {
  id: string;
  tracking_number: string;
  state: CustodyState;
  point_id: string;
  description: string;
  size_category: Size;
  version: number;
  service_total: string;
  due_at?: string | null;
  received_at?: string | null;
}

export type Registered = Custody & { public_reference?: string };

export interface Quote {
  tariff_id: string;
  amount: string;
  currency: "BOB";
  duration_hours: number;
}

export interface Location {
  id: string;
  point_id: string;
  code: string;
  state: "DISPONIBLE" | "OCUPADA" | "BLOQUEADA" | "FUERA_SERVICIO";
  size_category: Size;
  version: number;
}

export interface Credential {
  credential_id: string;
  code: string;
  expires_at: string;
}

export interface Authorization {
  authorization_id: string;
  custody_id: string;
  expires_at: string;
  state: "VALIDADA";
  location_code: string;
  description: string;
  version: number;
}

export interface Handover {
  id: string;
  custody_id: string;
  kind: "RETIRO" | "DEVOLUCION";
  confirmed_at: string;
  operator_id: string;
}

export interface Notification {
  id: string;
  subject: string;
  body: string;
  created_at: string;
  read_at?: string | null;
}

interface Tracking {
  state: "PENDIENTE" | "RECIBIDA" | "FINALIZADA";
  point_name: string;
  opening_hours: Record<string, unknown>;
}

export function custodyPath(id: string, operation?: string) {
  return "/custodies/" + encodeURIComponent(id) + (operation ? "/" + operation : "");
}

export const custodyApi = {
  points: () => request<Point[]>("/points"),
  quote: (pointId: string, size: Size, hours: number) =>
    request<Quote>("/points/" + encodeURIComponent(pointId) + "/quote?" + new URLSearchParams({
      size_category: size,
      duration_hours: String(hours),
    })),
  list: () => request<Custody[]>("/custodies"),
  detail: (id: string) => request<Custody>(custodyPath(id)),
  tracking: (reference: string) => request<Tracking>("/public-tracking/" + encodeURIComponent(reference)),
  rotate: (id: string) => mutate<{ public_reference: string }>(custodyPath(id, "public-reference")),
  issue: (id: string, reissue: boolean) => mutate<Credential>(custodyPath(id, "credentials"), { reissue }),
  inventory: (point: string) => request<Location[]>("/inventory?" + new URLSearchParams({ point_id: point })),
  notifications: () => request<Notification[]>("/notifications"),
  markRead: (id: string) => mutate<Resource>("/notifications/" + encodeURIComponent(id) + "/read"),
};

export const stateLabel: Record<CustodyState, string> = {
  REGISTRADA: "Registrada · pendiente de recepción",
  EN_CUSTODIA: "En custodia",
  RETIRO_EN_CURSO: "Retiro en curso",
  RETIRADA: "Retirada",
  DEVOLUCION_EN_CURSO: "Devolución en curso",
  DEVUELTA: "Devuelta",
  CANCELADA: "Cancelada",
};

export const sizeLabel: Record<Size, string> = { PEQUENO: "Pequeño", MEDIANO: "Mediano", GRANDE: "Grande" };

export function dateLabel(value: string) {
  return new Intl.DateTimeFormat("es-BO", {
    dateStyle: "medium", timeStyle: "short", timeZone: "America/La_Paz",
  }).format(new Date(value));
}
