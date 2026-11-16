import { useState, type ReactNode } from "react";

import { ApiError, request } from "../../services/api";
import { custodyApi, dateLabel, sizeLabel, sizes, type Location, type Point } from "../../services/custody";
import { WorkspaceBadge, WorkspaceEmpty, WorkspaceHeading } from "../dashboard/Workspace";
import { Field, formData, SizeGuide, SizeOptions, Status, useMutation, useTask, value } from "../shared/forms";
import { dailyScheduleFields, hoursFromForm, scheduleFields } from "../shared/hours";

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
  const [selection, setSelection] = useState("");
  const manual = !points.length || selection === "manual";

  return <>
    {points.length > 0 && <Field label="Punto de servicio" hint={"Elige el punto al que se aplicará esta operación."}>
      <select name={manual ? undefined : "point_id"} value={selection} required
        onChange={(event) => setSelection(event.target.value)}>
        <option value="">Elige un punto</option>
        {points.map((point) => <option key={point.id} value={point.id}>{point.name}</option>)}
        <option value="manual">Introducir otro identificador</option>
      </select>
    </Field>}
    {manual && <Field label="Identificador del punto" hint={"Copia el identificador completo del punto que quieres gestionar."} example={"Usa esta opción cuando el punto no aparezca en la lista. Necesitas un identificador de punto ya existente."}>
      <input name="point_id" required maxLength={36} />
    </Field>}
  </>;
}

function CommandForm({ heading, button, command, children, onSaved }: {
  heading: string; button: string; command: (data: FormData) => Command; children: ReactNode; onSaved?: () => void;
}) {
  const task = useTask();
  const send = useMutation();
  const [result, setResult] = useState<Reply>();

  return <details className="workspace-action-group">
    <summary>{heading}</summary>
    <form onSubmit={(event) => {
      const data = formData(event);
      setResult(undefined);
      void task.run(async () => {
        const { path, body, method } = command(data);
        setResult(await send<Reply>(path, body, method));
        onSaved?.();
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

function openingHours(data: FormData): Record<string, string> {
  const hours = hoursFromForm(data);
  if (!Object.keys(hours).length) {
    throw new ApiError(422, "HORARIO_INVALIDO", "Indica al menos un horario de atención.");
  }
  return hours;
}

function pointBody(data: FormData) {
  return { name: value(data, "name"), address: value(data, "address"), opening_hours: openingHours(data),
    is_active: data.has("active") };
}

function PointFields() {
  return <>
    <Field label="Nombre del punto" example={"BUZON Xpress Miraflores. Usa un nombre que permita reconocer el punto."} hint={"Nombre que se mostrará al público."}><input name="name" required maxLength={120} placeholder="Ej. BUZON Xpress Miraflores" /></Field>
    <Field label="Dirección" example={"Zona Miraflores, avenida principal, local 4. Añade una referencia útil para encontrar el punto."}><input name="address" required maxLength={255} placeholder="Zona, calle y referencia" /></Field>
    <fieldset className="workspace-hours">
      <legend>Horario publicado</legend>
      <p>Indica los intervalos de atención. Los días vacíos se omiten.</p>
      {scheduleFields.map(([field, label]) => <Field key={field} label={label} example="09:00–13:00 y 14:00–18:00. Deja vacío un día sin atención.">
        <input name={field} placeholder="09:00–17:00" maxLength={80} />
      </Field>)}
      <details>
        <summary>Horarios por día</summary>
        <p>Si los horarios cambian según el día, completa estos campos. Se usarán en lugar de los intervalos generales. Deja vacíos los días sin atención.</p>
        {dailyScheduleFields.map(([field, label]) => <Field key={field} label={label}
          example="09:00–13:00 y 14:00–18:00. Deja vacío si ese día no hay atención.">
          <input name={field} placeholder="09:00–17:00" maxLength={80} />
        </Field>)}
      </details>
    </fieldset>
    <label className="check"><input type="checkbox" name="active" defaultChecked /> Punto habilitado</label>
  </>;
}

function LocationsLookup({ points }: { points: Point[] }) {
  const task = useTask();
  const [locations, setLocations] = useState<Location[]>();

  return <details className="workspace-action-group">
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
    <Field label="Inicio de vigencia · hora de La Paz" hint={"Fecha y hora desde las que se aplicará la nueva tarifa."}><input type="datetime-local" name="valid_from" required /></Field>
    {sizes.map((size) => <fieldset key={size}>
      <legend>{sizeLabel[size]}</legend>
      <Field label="Horas cubiertas por la tarifa base" example={"Con 24, el importe base cubre las primeras 24 horas."}><input name={size + "_base_hours"} type="number" min={1} step={1} required /></Field>
      <Field label="Horas de cada bloque adicional" example={"Con 12, cada bloque adicional cubre otras 12 horas."}><input name={size + "_block_hours"} type="number" min={1} step={1} required /></Field>
      <Field label="Importe base BOB" hint={"En bolivianos: usa punto y dos decimales."} example={"Escribe 12.50 para un importe de doce bolivianos con cincuenta centavos."}><input name={size + "_base_amount"} inputMode="decimal" placeholder="0.00"
        pattern="[0-9]+\.[0-9]{2}" required /></Field>
      <Field label="Importe por bloque adicional BOB" hint={"En bolivianos: usa punto y dos decimales."} example={"Escribe 3.00 para cobrar tres bolivianos por cada bloque adicional."}><input name={size + "_block_amount"} inputMode="decimal" placeholder="0.00"
        pattern="[0-9]+\.[0-9]{2}" required /></Field>
    </fieldset>)}
  </>;
}

export function Administration({ points, onPointChange }: { points: Point[]; onPointChange: () => void }) {
  return <section aria-labelledby="admin-heading">
    <WorkspaceHeading id="admin-heading" title="Administración de puntos y personal"
      description="Elige qué parte del servicio quieres configurar. Cada cambio se aplica al punto indicado." />
    <div className="workspace-subgroups">
      <div className="workspace-config-column">
      <section className="workspace-subgroup" aria-labelledby="point-settings-heading">
        <h3 id="point-settings-heading">Puntos y horarios</h3>
        <p>Publica los datos y horarios que verá el público.</p>

        <CommandForm heading="Crear punto" button="Crear punto" onSaved={onPointChange}
          command={(data) => ({ path: "/admin/points", body: pointBody(data) })}>
          <PointFields />
        </CommandForm>

        <CommandForm heading="Actualizar un punto existente" button="Guardar punto" onSaved={onPointChange}
          command={(data) => ({ path: "/admin/points/" + encodeURIComponent(requiredPoint(data)), method: "PUT", body: pointBody(data) })}>
          <PointField points={points} /><PointFields />
        </CommandForm>

      </section>
      <section className="workspace-subgroup" aria-labelledby="location-settings-heading">
        <h3 id="location-settings-heading">Ubicaciones</h3>
        <p>Consulta la capacidad, crea ubicaciones o cambia su estado.</p>

        <LocationsLookup points={points} />
        <CommandForm heading="Crear ubicación" button="Crear ubicación" command={(data) => ({
          path: "/admin/locations",
          body: { point_id: requiredPoint(data), code: value(data, "code"), size_category: value(data, "size") },
        })}>
          <PointField points={points} />
          <Field label="Código interno de ubicación" hint={"Etiqueta que identifica un espacio dentro del punto."} example={"P-03 puede identificar el tercer espacio para objetos pequeños."}><input name="code" maxLength={24} required placeholder="Ej. P-03" /></Field>
          <Field label="Tamaño" hint={"Categoría de objetos que admite esta ubicación."}><select name="size"><SizeOptions /></select></Field><SizeGuide />
        </CommandForm>

        <CommandForm heading="Cambiar estado de una ubicación" button="Guardar estado" command={(data) => ({
          path: "/admin/locations/" + encodeURIComponent(value(data, "id")), method: "PATCH",
          body: { state: value(data, "state"), expected_version: Number(value(data, "version")), reason: value(data, "reason") },
        })}>
          <Field label="Identificador de ubicación" hint={"Cópialo de Consultar identificadores y versiones de ubicaciones."} example={"Selecciona el punto en esa consulta y copia el identificador completo de la ubicación que vas a cambiar."}><input name="id" required maxLength={36} /></Field>
          <Field label="Versión consultada" hint={"Usa la versión actual que aparece junto a la ubicación."} example={"Si la consulta muestra versión 2, escribe 2. Vuelve a consultar si otra persona modificó la ubicación."}><input type="number" name="version" min={1} step={1} required /></Field>
          <Field label="Nuevo estado" hint={"Estado que tendrá la ubicación cuando se guarde el cambio."}><select name="state">
            <option value="DISPONIBLE">Disponible</option><option value="BLOQUEADA">Bloqueada</option>
            <option value="FUERA_SERVICIO">Fuera de servicio</option>
          </select></Field>
          <Field label="Motivo del cambio" example={"Estante en mantenimiento hasta completar su revisión."}><textarea name="reason" required maxLength={500} /></Field>
        </CommandForm>

      </section>
      </div>
      <div className="workspace-config-column">
      <section className="workspace-subgroup" aria-labelledby="staff-settings-heading">
        <h3 id="staff-settings-heading">Personal y contactos</h3>
        <p>Gestiona asignaciones y comprobaciones presenciales.</p>

        <CommandForm heading="Asignar o revocar personal" button="Guardar asignación" command={(data) => ({
          path: "/admin/staff-assignments",
          body: { point_id: requiredPoint(data), user_id: value(data, "user"), role: value(data, "role"), is_active: data.has("active") },
        })}>
          <PointField points={points} />
          <Field label="Identificador autorizado de la cuenta" hint={"La persona lo encuentra en Mi cuenta → Identificador de mi cuenta."} example={"Copia el identificador completo que te proporcione la persona autorizada."}><input name="user" maxLength={36} required /></Field>
          <Field label="Rol" example={"Operador: atención del punto. Auditor: consulta de eventos e indicadores. Administrador: configuración y supervisión."}><select name="role">
            <option value="OPERADOR">Operador</option><option value="ADMIN">Administrador</option><option value="AUDITOR">Auditor</option>
          </select></Field>
          <label className="check"><input type="checkbox" name="active" defaultChecked /> Asignación activa</label>
        </CommandForm>

        <CommandForm heading="Comprobar contacto presencialmente" button="Registrar comprobación" command={(data) => ({
          path: "/admin/users/" + encodeURIComponent(value(data, "user")) + "/verify-contact",
          body: { reason: value(data, "reason") },
        })}>
          <Field label="Identificador autorizado de la cuenta" hint={"La persona lo encuentra en Mi cuenta → Identificador de mi cuenta."} example={"Copia el identificador completo que te proporcione la persona autorizada."}><input name="user" maxLength={36} required /></Field>
          <Field label="Evidencia mínima de comprobación" hint={"Describe cómo se comprobó el contacto con la persona presente."} example={"Cuenta presente en el punto y contacto comprobado con su titular. Registra solo la evidencia necesaria."}><textarea name="reason" maxLength={500} required /></Field>
        </CommandForm>

      </section>
      <section className="workspace-subgroup" aria-labelledby="tariff-settings-heading">
        <h3 id="tariff-settings-heading">Tarifas</h3>
        <p>Define una versión por tamaño y bloque de tiempo.</p>

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
      </section>
      </div>
    </div>
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
      <WorkspaceHeading id="audit-heading" title="Eventos de auditoría"
        description="Consulta un punto y filtra los eventos recibidos por tipo o correlación." />
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
      {events && <Field label="Filtrar eventos consultados por tipo o correlación" example={"Escribe una parte del tipo de evento o pega su identificador de correlación."}>
        <input value={filter} onChange={(event) => setFilter(event.target.value)} />
      </Field>}
      <ul className="items workspace-records">{visible?.map((event) => <li key={event.id}>
        <div className="workspace-record-top"><strong>{event.event_type.replaceAll("_", " ")}</strong>
          <WorkspaceBadge>{dateLabel(event.created_at)}</WorkspaceBadge></div>
        <p>Correlación <code>{event.correlation_id}</code></p>
        {event.actor_id && <p>Actor <code>{event.actor_id}</code></p>}
        {event.custody_id && <p>Custodia <code>{event.custody_id}</code></p>}
      </li>)}</ul>
      {visible?.length === 0 && <WorkspaceEmpty icon="audit" title="Sin eventos para esta consulta"
        description="Revisa el punto o cambia el filtro de resultados." />}
    </section>
    <section aria-labelledby="reports-heading">
      <WorkspaceHeading id="reports-heading" title="Indicadores del punto"
        description="Define el periodo antes de consultar los indicadores o exportarlos." />
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
        <Field label="Desde · fecha incluida en La Paz" hint={"Se incluyen los registros desde el inicio de este día."}><input type="date" name="from" required /></Field>
        <Field label="Hasta · fecha no incluida en La Paz" hint={"El periodo termina al comenzar este día."} example={"Para incluir todo el 7 de noviembre, selecciona el 8 de noviembre como fecha final."}><input type="date" name="to" required /></Field>
        <button type="submit" disabled={reportTask.busy}>Consultar indicadores</button>
      </form>
      <Status {...reportTask} />
      {report && <div className="receipt">
        <p>{dateLabel(report.from)} a {dateLabel(report.to)}.</p>
        <dl className="details workspace-fact-grid">
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
