import { useId, useState, type ReactNode } from "react";

import { ApiError, request } from "../../services/api";
import { custodyApi, dateLabel, sizeLabel, sizes, type Location, type Point } from "../../services/custody";
import { Field, formData, SizeOptions, Status, useMutation, useTask, value } from "../shared/forms";

type Method = "POST" | "PUT" | "PATCH";
interface Command {
  path: string;
  body: object;
  method?: Method;
}
interface Reply {
  id: string;
  state?: string;
}

function PointField({ points }: { points: Point[] }) {
  const id = useId();
  return <Field label="Identificador del punto">
    <input name="point_id" list={id} required maxLength={36} />
    <datalist id={id}>{points.map((point) => <option key={point.id} value={point.id}>{point.name}</option>)}</datalist>
  </Field>;
}

function CommandForm({ heading, button, command, children }: {
  heading: string; button: string; command: (data: FormData) => Command; children: ReactNode;
}) {
  const task = useTask();
  const send = useMutation();
  const [result, setResult] = useState<Reply>();

  return <details>
    <summary>{heading}</summary>
    <form onSubmit={(event) => {
      const data = formData(event);
      setResult(undefined);
      void task.run(async () => {
        const { path, body, method } = command(data);
        setResult(await send<Reply>(path, body, method));
      });
    }} aria-busy={task.busy}>
      {children}
      <button type="submit" disabled={task.busy}>{button}</button>
    </form>
    <Status {...task} />
    {result && <p className="receipt" role="status">Guardado · <code>{result.id}</code>{result.state ? " · " + result.state : ""}</p>}
  </details>;
}

function requiredPoint(data: FormData) {
  return value(data, "point_id");
}

function openingHours(data: FormData): Record<string, unknown> {
  try {
    const hours: unknown = JSON.parse(value(data, "opening_hours"));
    if (hours && typeof hours === "object" && !Array.isArray(hours)) return hours as Record<string, unknown>;
  } catch {
    // The same correction applies to invalid JSON and JSON of the wrong kind.
  }
  throw new ApiError(422, "HORARIO_INVALIDO", 'Escribe el horario como objeto JSON, por ejemplo {"lunes":"09:00–17:00"}.');
}

function pointBody(data: FormData) {
  return { name: value(data, "name"), address: value(data, "address"), opening_hours: openingHours(data),
    is_active: data.has("active") };
}

function PointFields() {
  return <>
    <Field label="Nombre del punto"><input name="name" required maxLength={120} /></Field>
    <Field label="Dirección"><input name="address" required maxLength={255} /></Field>
    <Field label="Horario publicado como JSON">
      <textarea name="opening_hours" placeholder={'{"lunes":"09:00–17:00"}'} required />
    </Field>
    <label className="check"><input type="checkbox" name="active" defaultChecked /> Punto habilitado</label>
  </>;
}

function LocationsLookup({ points }: { points: Point[] }) {
  const task = useTask();
  const [locations, setLocations] = useState<Location[]>();

  return <details>
    <summary>Consultar identificadores y versiones de ubicaciones</summary>
    <form onSubmit={(event) => {
      const data = formData(event);
      setLocations(undefined);
      void task.run(async () => setLocations(await custodyApi.inventory(requiredPoint(data))));
    }}>
      <PointField points={points} />
      <button type="submit" className="secondary" disabled={task.busy}>Consultar ubicaciones</button>
    </form>
    <Status {...task} />
    {locations && <ul className="items">{locations.map((location) => <li key={location.id}>
      <strong>{location.code}</strong> · {location.state} · versión {location.version}
      <p><code>{location.id}</code></p>
    </li>)}</ul>}
    {locations?.length === 0 && <p>El punto no tiene ubicaciones registradas.</p>}
  </details>;
}

function localDateTime(date: string) {
  return new Date(date + "-04:00").toISOString();
}

function TariffFields() {
  return <>
    <Field label="Inicio de vigencia · hora de La Paz"><input type="datetime-local" name="valid_from" required /></Field>
    {sizes.map((size) => <fieldset key={size}>
      <legend>{sizeLabel[size]}</legend>
      <Field label="Horas cubiertas por la tarifa base"><input name={size + "_base_hours"} type="number" min={1} step={1} required /></Field>
      <Field label="Horas de cada bloque adicional"><input name={size + "_block_hours"} type="number" min={1} step={1} required /></Field>
      <Field label="Importe base BOB"><input name={size + "_base_amount"} inputMode="decimal" placeholder="0.00"
        pattern="[0-9]+\.[0-9]{2}" required /></Field>
      <Field label="Importe por bloque adicional BOB"><input name={size + "_block_amount"} inputMode="decimal" placeholder="0.00"
        pattern="[0-9]+\.[0-9]{2}" required /></Field>
    </fieldset>)}
  </>;
}

export function Administration({ points }: { points: Point[] }) {
  return <section aria-labelledby="admin-heading">
    <h2 id="admin-heading">Administración de puntos y personal</h2>
    <p>El servidor vuelve a comprobar tus permisos y la ocupación del punto en cada cambio.</p>

    <CommandForm heading="Crear punto" button="Crear punto" command={(data) => ({ path: "/admin/points", body: pointBody(data) })}>
      <PointFields />
    </CommandForm>

    <CommandForm heading="Actualizar un punto existente" button="Guardar punto"
      command={(data) => ({ path: "/admin/points/" + encodeURIComponent(requiredPoint(data)), method: "PUT", body: pointBody(data) })}>
      <PointField points={points} /><PointFields />
    </CommandForm>

    <LocationsLookup points={points} />
    <CommandForm heading="Crear ubicación" button="Crear ubicación" command={(data) => ({
      path: "/admin/locations",
      body: { point_id: requiredPoint(data), code: value(data, "code"), size_category: value(data, "size") },
    })}>
      <PointField points={points} />
      <Field label="Código interno de ubicación"><input name="code" maxLength={24} required /></Field>
      <Field label="Tamaño"><select name="size"><SizeOptions /></select></Field>
    </CommandForm>

    <CommandForm heading="Cambiar estado de una ubicación" button="Guardar estado" command={(data) => ({
      path: "/admin/locations/" + encodeURIComponent(value(data, "id")), method: "PATCH",
      body: { state: value(data, "state"), expected_version: Number(value(data, "version")), reason: value(data, "reason") },
    })}>
      <Field label="Identificador de ubicación"><input name="id" required maxLength={36} /></Field>
      <Field label="Versión consultada"><input type="number" name="version" min={1} step={1} required /></Field>
      <Field label="Nuevo estado"><select name="state">
        <option value="DISPONIBLE">Disponible</option><option value="BLOQUEADA">Bloqueada</option>
        <option value="FUERA_SERVICIO">Fuera de servicio</option>
      </select></Field>
      <Field label="Motivo del cambio"><textarea name="reason" required maxLength={500} /></Field>
    </CommandForm>

    <CommandForm heading="Asignar o revocar personal" button="Guardar asignación" command={(data) => ({
      path: "/admin/staff-assignments",
      body: { point_id: requiredPoint(data), user_id: value(data, "user"), role: value(data, "role"), is_active: data.has("active") },
    })}>
      <PointField points={points} />
      <Field label="Identificador autorizado de la cuenta"><input name="user" maxLength={36} required /></Field>
      <Field label="Rol"><select name="role">
        <option value="OPERADOR">Operador</option><option value="ADMIN">Administrador</option><option value="AUDITOR">Auditor</option>
      </select></Field>
      <label className="check"><input type="checkbox" name="active" defaultChecked /> Asignación activa</label>
    </CommandForm>

    <CommandForm heading="Comprobar contacto presencialmente" button="Registrar comprobación" command={(data) => ({
      path: "/admin/users/" + encodeURIComponent(value(data, "user")) + "/verify-contact",
      body: { reason: value(data, "reason") },
    })}>
      <Field label="Identificador autorizado de la cuenta"><input name="user" maxLength={36} required /></Field>
      <Field label="Evidencia mínima de comprobación"><textarea name="reason" maxLength={500} required /></Field>
    </CommandForm>

    <CommandForm heading="Publicar versión de tarifa" button="Publicar nueva tarifa" command={(data) => ({
      path: "/admin/tariffs",
      body: {
        point_id: requiredPoint(data),
        valid_from: localDateTime(value(data, "valid_from")),
        rules: {
          currency: "BOB",
          sizes: Object.fromEntries(sizes.map((size) => [size, {
            base_hours: Number(value(data, size + "_base_hours")),
            block_hours: Number(value(data, size + "_block_hours")),
            base_amount: value(data, size + "_base_amount"),
            block_amount: value(data, size + "_block_amount"),
          }])),
        },
      },
    })}>
      <PointField points={points} /><TariffFields />
    </CommandForm>
  </section>;
}

interface AuditEvent {
  id: string;
  event_type: string;
  created_at: string;
  correlation_id: string;
  actor_id?: string | null;
  custody_id?: string | null;
}

interface PointReport {
  point_id: string;
  from: string;
  to: string;
  available_locations: number;
  occupied_locations: number;
  completed_custodies: number;
  data_quality_note: string;
}

function downloadReport(report: PointReport) {
  const quote = (value: string | number) => {
    const text = String(value);
    const safe = /^[=+@-]|^[\\t\\r\\n]/.test(text) ? "'" + text : text;
    return '"' + safe.replaceAll('"', '""') + '"';
  };
  const rows = [
    ["Punto", "Desde", "Hasta", "Ubicaciones disponibles", "Ubicaciones ocupadas", "Custodias completadas", "Calidad de datos"],
    [report.point_id, report.from, report.to, report.available_locations, report.occupied_locations,
      report.completed_custodies, report.data_quality_note],
  ];
  const csv = rows.map((row) => row.map(quote).join(",")).join("\\r\\n");
  const url = URL.createObjectURL(new Blob(["\\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "buzon-indicadores.csv";
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function Audit({ points }: { points: Point[] }) {
  const audit = useTask();
  const reportTask = useTask();
  const [events, setEvents] = useState<AuditEvent[]>();
  const [report, setReport] = useState<PointReport>();
  const [filter, setFilter] = useState("");
  const visible = events?.filter((event) =>
    [event.event_type, event.correlation_id].some((entry) => entry.toLowerCase().includes(filter.trim().toLowerCase())));

  return <div className="dashboard-grid">
    <section aria-labelledby="audit-heading">
      <h2 id="audit-heading">Eventos de auditoría</h2>
      <p>Consulta eventos recientes del punto. Los filtros se aplican a los resultados recibidos.</p>
      <form onSubmit={(event) => {
        const data = formData(event);
        setEvents(undefined);
        void audit.run(async () => setEvents(await request<AuditEvent[]>("/audit/events?"
          + new URLSearchParams({ point_id: requiredPoint(data) }))));
      }}>
        <PointField points={points} />
        <button type="submit" disabled={audit.busy}>Consultar eventos</button>
      </form>
      <Status {...audit} />
      {events && <Field label="Filtrar eventos consultados por tipo o correlación">
        <input value={filter} onChange={(event) => setFilter(event.target.value)} />
      </Field>}
      <ul className="items">{visible?.map((event) => <li key={event.id}>
        <strong>{event.event_type}</strong> · {dateLabel(event.created_at)}
        <p>Correlación <code>{event.correlation_id}</code></p>
        {event.actor_id && <p>Actor <code>{event.actor_id}</code></p>}
        {event.custody_id && <p>Custodia <code>{event.custody_id}</code></p>}
      </li>)}</ul>
      {visible?.length === 0 && <p>Sin eventos en la consulta.</p>}
    </section>
    <section aria-labelledby="reports-heading">
      <h2 id="reports-heading">Indicadores del punto</h2>
      <form onSubmit={(event) => {
        const data = formData(event);
        setReport(undefined);
        void reportTask.run(async () => setReport(await request<PointReport>("/reports?" + new URLSearchParams({
          point_id: requiredPoint(data),
          from: localDateTime(value(data, "from") + "T00:00"),
          to: localDateTime(value(data, "to") + "T00:00"),
        }))));
      }}>
        <PointField points={points} />
        <Field label="Desde · fecha incluida en La Paz"><input type="date" name="from" required /></Field>
        <Field label="Hasta · fecha no incluida en La Paz"><input type="date" name="to" required /></Field>
        <button type="submit" disabled={reportTask.busy}>Consultar indicadores</button>
      </form>
      <Status {...reportTask} />
      {report && <div className="receipt">
        <p>{dateLabel(report.from)} a {dateLabel(report.to)}.</p>
        <dl className="details">
          <div><dt>Ubicaciones disponibles</dt><dd>{report.available_locations}</dd></div>
          <div><dt>Ubicaciones ocupadas</dt><dd>{report.occupied_locations}</dd></div>
          <div><dt>Custodias completadas</dt><dd>{report.completed_custodies}</dd></div>
        </dl>
        <p>{report.data_quality_note}</p>
        <button type="button" className="secondary" onClick={() => downloadReport(report)}>Descargar indicadores en CSV</button>
      </div>}
    </section>
  </div>;
}
