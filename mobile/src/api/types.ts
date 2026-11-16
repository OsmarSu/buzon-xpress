export type Role = "USUARIO" | "OPERADOR" | "ADMIN" | "AUDITOR";
export interface User { id: string; full_name: string; role: Role; contact_verified: boolean; mfa_enabled: boolean }
export interface MobileSession { user: User; access_token: string; expires_at: string; token_type: "Bearer" }
export interface MfaChallenge { mfa_required: true; challenge_token: string; expires_at: string }
export interface Point { id: string; name: string; address: string; opening_hours: Record<string, unknown>; is_active: boolean }
export type Size = "PEQUENO" | "MEDIANO" | "GRANDE";
export type CustodyState = "REGISTRADA" | "EN_CUSTODIA" | "RETIRO_EN_CURSO" | "RETIRADA" | "DEVOLUCION_EN_CURSO" | "DEVUELTA" | "CANCELADA";
export interface Custody { id: string; tracking_number: string; state: CustodyState; point_id: string; description: string; size_category: Size; version: number; service_total: string; due_at?: string | null; received_at?: string | null }
export interface Registered extends Custody { public_reference?: string }
export interface Quote { tariff_id: string; amount: string; currency: "BOB"; duration_hours: number }
export interface Notice { id: string; subject: string; body: string; created_at: string; read_at?: string | null }
export interface Credential { credential_id: string; code: string; expires_at: string }
export interface Tracking { state: "PENDIENTE" | "RECIBIDA" | "FINALIZADA"; point_name: string; opening_hours: Record<string, unknown> }
export interface Resource { id: string; state: string }
export const stateLabels: Record<CustodyState, string> = {
  REGISTRADA: "Pendiente de recepción", EN_CUSTODIA: "En custodia", RETIRO_EN_CURSO: "Retiro en curso",
  RETIRADA: "Retirada", DEVOLUCION_EN_CURSO: "Devolución en curso", DEVUELTA: "Devuelta", CANCELADA: "Cancelada",
};
export const sizes: { value: Size; label: string }[] = [
  { value: "PEQUENO", label: "Pequeño · hasta 30 × 20 × 15 cm" },
  { value: "MEDIANO", label: "Mediano · hasta 50 × 40 × 30 cm" },
  { value: "GRANDE", label: "Grande · hasta 70 × 50 × 50 cm" },
];
export const sizeMeasurementNote = "Medidas máximas con embalaje, en largo × ancho × alto. Elige el menor tamaño que admita el objeto.";
export function dateLabel(value: string) {
  return new Intl.DateTimeFormat("es-BO", { dateStyle: "medium", timeStyle: "short", timeZone: "America/La_Paz" }).format(new Date(value));
}
