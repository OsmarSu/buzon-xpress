import { useEffect, useRef, useState } from "react";

import { custodyApi, custodyPath, dateLabel, sizeLabel, stateLabel, type Credential, type Custody, type Point, type Quote, type Registered, type Size } from "../../services/custody";
import { WorkspaceBadge, WorkspaceEmpty, WorkspaceGlyph, WorkspaceHeading } from "../dashboard/Workspace";
import { CustodyExceptions } from "../operations/Exceptions";
import { Field, formData, SizeOptions, Status, useMutation, useTask, value } from "../shared/forms";

function CustodyStateBadge({ state }: { state: Custody["state"] }) {
  const tone = state === "EN_CUSTODIA" ? "info"
    : state === "RETIRADA" || state === "DEVUELTA" ? "good"
    : state.endsWith("EN_CURSO") ? "pending" : "neutral";
  return <WorkspaceBadge tone={tone}>{stateLabel[state]}</WorkspaceBadge>;
}

export function CustodySummary({ custody, point }: { custody: Custody; point?: Point }) {
  return <dl className="details workspace-fact-grid">
    <div><dt>Guía privada</dt><dd>{custody.tracking_number}</dd></div>
    <div><dt>Estado</dt><dd><CustodyStateBadge state={custody.state} /></dd></div>
    <div><dt>Descripción</dt><dd>{custody.description}</dd></div>
    <div><dt>Tamaño</dt><dd>{sizeLabel[custody.size_category]}</dd></div>
    <div><dt>Punto</dt><dd>{point?.name ?? custody.point_id}</dd></div>
    <div><dt>Importe de servicio</dt><dd>{custody.state === "REGISTRADA" ? "Por confirmar en recepción" : custody.service_total + " BOB"}</dd></div>
    {custody.received_at && <div><dt>Recepción</dt><dd>{dateLabel(custody.received_at)}</dd></div>}
    {custody.due_at && <div><dt>Plazo</dt><dd>{dateLabel(custody.due_at)} · La Paz</dd></div>}
    <div><dt>Identificador</dt><dd><code>{custody.id}</code></dd></div>
  </dl>;
}

function PublicReference({ reference, onDismiss }: { reference: string; onDismiss: () => void }) {
  return <div className="receipt">
    <strong>Referencia pública nueva</strong>
    <p>Guárdala para consultar el estado. La guía privada y el código de retiro son distintos.</p>
    <p><code>{reference}</code></p>
    <button type="button" className="secondary" onClick={onDismiss}>Ocultar referencia</button>
  </div>;
}

function RegisterCustody({ points, onCreated }: { points: Point[]; onCreated: (custody: Custody) => void }) {
  const task = useTask();
  const send = useMutation();
  const [pointId, setPoint] = useState("");
  const [size, setSize] = useState<Size>("PEQUENO");
  const [hours, setHours] = useState("24");
  const [quote, setQuote] = useState<Quote>();
  const [created, setCreated] = useState<Registered>();
  const selectedPoint = points.find((point) => point.id === pointId);

  return <section aria-labelledby="register-custody-heading">
    <WorkspaceHeading id="register-custody-heading" title="Registrar un objeto"
      description="Indica el punto y el destinatario. La ubicación y el importe final se confirman al recibir el bulto." />
    {points.length ? <form onSubmit={(event) => {
      const form = event.currentTarget;
      const fields = formData(event);
      const body = {
        point_id: pointId,
        size_category: size,
        recipient_contact: value(fields, "recipient"),
        description: value(fields, "description"),
      };
      void task.run(async () => {
        const result = await send<Registered>("/custodies", body);
        setCreated(result);
        onCreated(result);
        form.reset();
      });
    }} aria-busy={task.busy}>
      <Field label="Punto de servicio">
        <select value={pointId} required disabled={task.busy}
          onChange={(event) => { setPoint(event.target.value); setQuote(undefined); }}>
          <option value="">Elige un punto activo</option>
          {points.map((point) => <option key={point.id} value={point.id}>{point.name}</option>)}
        </select>
      </Field>
      {selectedPoint && <div className="workspace-context">
        <WorkspaceGlyph name="pin" /><p>{selectedPoint.address}</p>
      </div>}
      <Field label="Tamaño declarado">
        <select value={size} disabled={task.busy}
          onChange={(event) => { setSize(event.target.value as Size); setQuote(undefined); }}><SizeOptions /></select>
      </Field>
      <Field label="Contacto exacto del destinatario registrado">
        <input name="recipient" autoComplete="off" required maxLength={254} />
      </Field>
      <Field label="Descripción externa del objeto">
        <textarea name="description" required maxLength={255} />
      </Field>
      <Field label="Horas para cotizar (referencia)">
        <input type="number" min={1} step={1} value={hours} disabled={task.busy}
          onChange={(event) => { setHours(event.target.value); setQuote(undefined); }} />
      </Field>
      <button type="button" className="secondary" disabled={task.busy || !selectedPoint || !Number.isInteger(Number(hours)) || Number(hours) < 1}
        onClick={() => void task.run(async () => setQuote(await custodyApi.quote(pointId, size, Number(hours))))}>
        Consultar tarifa
      </button>
      {quote && <p className="receipt" role="status">
        Cotización de referencia de <strong>{quote.amount} BOB</strong> por {quote.duration_hours} horas.
      </p>}
      <button type="submit" disabled={task.busy}>Registrar objeto</button>
    </form> : <WorkspaceEmpty icon="pin" title="No hay puntos para el registro"
      description="Vuelve a consultar los puntos cuando se publique un horario de atención." />}
    <Status {...task} message={created ? "Objeto registrado. Preséntalo al operador dentro del horario de atención." : undefined} />
    {created?.public_reference && <PublicReference reference={created.public_reference}
      onDismiss={() => setCreated({ ...created, public_reference: undefined })} />}
  </section>;
}

function ParticipantActions({ custody, onUpdate }: { custody: Custody; onUpdate: (next: Custody) => void }) {
  const task = useTask();
  const send = useMutation();
  const [credential, setCredential] = useState<Credential>();
  const [reference, setReference] = useState<string>();
  const [notice, setNotice] = useState("");
  const [confirmRotation, setConfirmRotation] = useState(false);
  const [confirmReissue, setConfirmReissue] = useState(false);

  useEffect(() => {
    if (!credential) return;
    const remaining = new Date(credential.expires_at).getTime() - Date.now();
    const timeout = window.setTimeout(() => {
      setCredential(undefined);
      setNotice("El código venció. Verifica las opciones de la custodia.");
    }, Math.max(0, remaining));
    return () => window.clearTimeout(timeout);
  }, [credential]);

  return <>
    {custody.state === "REGISTRADA" && <details className="workspace-action-group">
      <summary>Cancelar el registro si eres emisor</summary>
      <form onSubmit={(event) => {
        const fields = formData(event);
        void task.run(async () => {
          onUpdate(await send<Custody>(custodyPath(custody.id, "cancel"), {
            expected_version: custody.version, reason: value(fields, "reason"),
          }));
          setNotice("Registro cancelado.");
        });
      }}>
        <Field label="Motivo de la cancelación"><input name="reason" required maxLength={255} /></Field>
        <button type="submit" disabled={task.busy}>Cancelar registro</button>
      </form>
    </details>}

    {custody.state === "EN_CUSTODIA" && <details className="workspace-action-group" open={credential ? true : undefined}>
      <summary>Obtener código temporal si eres destinatario</summary>
      <p>Muéstralo únicamente al operador al recoger el objeto. Se borra al salir de este detalle.</p>
      <div className="actions">
        <button type="button" disabled={task.busy || credential !== undefined} onClick={() => void task.run(async () => {
          setCredential(await custodyApi.issue(custody.id, false));
          setNotice("Código temporal emitido.");
        })}>Emitir código</button>
        <button className="secondary" type="button" disabled={task.busy} onClick={() => setConfirmReissue(!confirmReissue)}>
          Reemitir código
        </button>
      </div>
      {confirmReissue && <div className="warning">
        <p>La reemisión invalida el código anterior.</p>
        <button type="button" disabled={task.busy} onClick={() => void task.run(async () => {
          setCredential(await custodyApi.issue(custody.id, true));
          setConfirmReissue(false);
          setNotice("Código anterior reemplazado.");
        })}>Confirmar reemisión</button>
        <button type="button" className="secondary" disabled={task.busy}
          onClick={() => setConfirmReissue(false)}>Conservar código</button>
      </div>}
      {credential && <div className="receipt">
        <p className="secret">{credential.code}</p>
        <p>Vence {dateLabel(credential.expires_at)}.</p>
        <button type="button" className="secondary" onClick={() => setCredential(undefined)}>Ocultar código</button>
      </div>}
    </details>}

    <details className="workspace-action-group" open={reference ? true : undefined}>
      <summary>Renovar referencia pública</summary>
      <p>Esta acción invalida el enlace público anterior.</p>
      {confirmRotation ? <div className="actions"><button type="button" disabled={task.busy} onClick={() => void task.run(async () => {
        setReference((await custodyApi.rotate(custody.id)).public_reference);
        setConfirmRotation(false);
      })}>Confirmar nueva referencia</button>
        <button type="button" className="secondary" disabled={task.busy}
          onClick={() => setConfirmRotation(false)}>Conservar referencia</button>
      </div> : <button type="button" className="secondary" disabled={task.busy} onClick={() => setConfirmRotation(true)}>
          Preparar renovación
        </button>}
      {reference && <PublicReference reference={reference} onDismiss={() => setReference(undefined)} />}
    </details>
    <Status {...task} message={notice} />
  </>;
}

export function Participant({ points, openId, setOpenId, verified }: {
  points: Point[]; openId: string | null; setOpenId: (id: string | null) => void; verified: boolean;
}) {
  const [items, setItems] = useState<Custody[]>([]);
  const [selected, setSelected] = useState<Custody>();
  const [filter, setFilter] = useState("");
  const listTask = useTask();
  const detailTask = useTask();
  const detailTrigger = useRef<HTMLButtonElement | null>(null);

  function load() {
    void listTask.run(async () => setItems(await custodyApi.list()));
  }
  useEffect(load, []);
  useEffect(() => {
    setSelected(undefined);
    detailTask.setError("");
    if (openId) {
      document.getElementById("detail-heading")?.focus();
      let current = true;
      // Details may change while a response for the previous selection is still in flight.
      void custodyApi.detail(openId).then((item) => { if (current) setSelected(item); })
        .catch((error: unknown) => {
          if (current) void detailTask.run(async () => { throw error; });
        });
      return () => { current = false; };
    }
  }, [openId]);

  function update(item: Custody) {
    setSelected(item);
    setItems((list) => list.some((existing) => existing.id === item.id)
      ? list.map((existing) => existing.id === item.id ? item : existing) : [item, ...list]);
  }

  function closeDetail() {
    setOpenId(null);
    const trigger = detailTrigger.current;
    if (trigger?.isConnected) trigger.focus();
    else document.getElementById("mine-heading")?.focus();
  }

  const currentDetail = selected?.id === openId ? selected : undefined;
  const visible = items.filter((item) => !filter || item.state === filter);
  return <div className="dashboard-grid">
    <section aria-labelledby="mine-heading">
      <WorkspaceHeading id="mine-heading" title="Mis custodias" description="Encuentra tus registros por estado y abre su detalle."
        action={<button type="button" className="secondary workspace-quiet-action" disabled={listTask.busy} onClick={load}>
          <WorkspaceGlyph name="refresh" /> Actualizar custodias
        </button>} />
      <Field label="Filtrar por estado">
        <select value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="">Todos los estados</option>
          {Object.entries(stateLabel).map(([state, label]) => <option key={state} value={state}>{label}</option>)}
        </select>
      </Field>
      <Status {...listTask} />
      <ul className="items workspace-records">{visible.map((item) => <li key={item.id}>
        <div className="workspace-record-top"><strong>{item.description}</strong><CustodyStateBadge state={item.state} /></div>
        <p className="workspace-meta">{item.tracking_number}{item.due_at ? " · Plazo " + dateLabel(item.due_at) : ""}</p>
        <button type="button" className="secondary workspace-quiet-action"
          onClick={(event) => { detailTrigger.current = event.currentTarget; setOpenId(item.id); }}>
          Ver detalle de {item.tracking_number} <WorkspaceGlyph name="chevron" />
        </button>
      </li>)}</ul>
      {!visible.length && !listTask.busy && !listTask.error && <WorkspaceEmpty
        title={filter ? "Sin resultados para este estado" : "Aún no tienes custodias"}
        description={filter ? "Prueba con otro estado para volver a ver tus registros." : "Registra un objeto o espera a que alguien lo registre para ti."} />}
    </section>

    {verified ? <RegisterCustody points={points} onCreated={(item) => { update(item); setOpenId(item.id); }} />
      : <section aria-labelledby="verify-before-register">
        <WorkspaceHeading id="verify-before-register" title="Registrar un objeto" />
        <WorkspaceEmpty title="Comprueba tu contacto"
          description="Abre el enlace de tu correo o solicita la comprobación en un punto atendido para registrar una custodia." />
      </section>}

    {openId && <section className="full-width" aria-labelledby="detail-heading">
      <WorkspaceHeading id="detail-heading" title="Detalle privado"
        action={<button type="button" className="secondary" onClick={closeDetail}>Cerrar detalle</button>} />
      <Status {...detailTask} busy={!currentDetail && !detailTask.error} />
      {currentDetail && <>
        <CustodySummary custody={currentDetail} point={points.find((point) => point.id === currentDetail.point_id)} />
        <ParticipantActions key={"actions-" + currentDetail.id} custody={currentDetail} onUpdate={update} />
        <CustodyExceptions key={"exceptions-" + currentDetail.id} custody={currentDetail} />
      </>}
    </section>}
  </div>;
}
