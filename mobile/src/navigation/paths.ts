import type { Size } from "../api/types";
export type PersonalPath = "/" | "/custodias" | "/puntos" | "/avisos" | "/cuenta";
const personalPaths = new Set<PersonalPath>(["/", "/custodias", "/puntos", "/avisos", "/cuenta"]);
export function safeReturnPath(value: string | string[] | undefined): PersonalPath {
  return typeof value === "string" && personalPaths.has(value as PersonalPath) ? value as PersonalPath : "/";
}
export function custodyId(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value) ? value : undefined;
}

export interface RegistrationDraft { pointId: string; size: Size; hours: string }
export function registrationDraft(point: unknown, size: unknown, hours: unknown): RegistrationDraft | undefined {
  if (typeof point !== "string" || !custodyId(point)) return undefined;
  if (typeof size !== "string" || !["PEQUENO", "MEDIANO", "GRANDE"].includes(size)) return undefined;
  if (typeof hours !== "string" || !/^[0-9]{1,6}$/.test(hours) || Number(hours) < 1) return undefined;
  return { pointId: point, size: size as Size, hours: String(Number(hours)) };
}
