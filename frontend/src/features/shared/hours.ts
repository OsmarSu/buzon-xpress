export const scheduleFields = [
  ["weekdays", "Lunes a viernes"], ["saturday", "Sábado"], ["sunday", "Domingo"],
] as const;

export const dailyScheduleFields = [
  ["day_monday", "Lunes"], ["day_tuesday", "Martes"], ["day_wednesday", "Miércoles"],
  ["day_thursday", "Jueves"], ["day_friday", "Viernes"], ["day_saturday", "Sábado"],
  ["day_sunday", "Domingo"],
] as const;

export function hoursFromForm(data: FormData): Record<string, string> {
  const collect = (fields: readonly (readonly [string, string])[]) => Object.fromEntries(
    fields.map(([field, label]) => [label, String(data.get(field) ?? "").trim()])
      .filter(([, schedule]) => schedule),
  );
  const daily = collect(dailyScheduleFields);
  return Object.keys(daily).length ? daily : collect(scheduleFields);
}

export function scheduleText(schedule: unknown): string {
  if (typeof schedule === "string" && schedule.trim()) return schedule;
  if (Array.isArray(schedule) && schedule.length && schedule.every((entry) => typeof entry === "string")) {
    return schedule.join(" · ");
  }
  return "Consulta el horario con el personal del punto.";
}
