import { useEffect, useState } from "react";

import { custodyApi, custodyPath, dateLabel, sizeLabel, stateLabel, type Credential, type Custody, type Point, type Quote, type Registered, type Size } from "../../services/custody";
import { CustodyExceptions } from "../operations/Exceptions";
import { Field, formData, SizeOptions, Status, useMutation, useTask, value } from "../shared/forms";

export function CustodySummary({ custody, point }: { custody: Custody; point?: Point }) {
  return <dl className="details">
    <div><dt>Guía privada</dt><dd>{custody.tracking_number}</dd></div>
    <div><dt>Estado</dt><dd>{stateLabel[custody.state]}</dd></div>
    <div><dt>Descripción</dt><dd>{custody.description}</dd></div>
    <div><dt>Tamaño</dt><dd>{sizeLabel[custody.size_category]}</dd></div>
    <div><dt>Punto</dt><dd>{point?.name ?? custody.point_id}</dd></div>
    <div><dt>Importe de servicio</dt><dd>{custody.service_total} BOB</dd></div>
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
    <h2 id="register-custody-heading">Registrar un objeto</h2>
    <p>El espacio se confirma cuando el operador recibe el objeto.</p>
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
      {selectedPoint && <p>{selectedPoint.address}</p>}
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
      {quote && <p role="status">Cotización de referencia de {quote.amount} BOB por {quote.duration_hours} horas.</p>}
      <button type="submit" disabled={task.busy}>Registrar objeto</button>
    </form> : <p>Se requiere un punto activo para registrar.</p>}
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
    {custody.state === "REGISTRADA" && <details>
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
        <Field label="Motivo de la cancelación"><input name="reason" required maxLength={500} /></Field>
        <button type="submit" disabled={task.busy}>Cancelar registro</button>
      </form>
    </details>}

    {custody.state === "EN_CUSTODIA" && <details open={credential ? true : undefined}>
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
      </div>}
      {credential && <div className="receipt">
        <p className="secret">{credential.code}</p>
        <p>Vence {dateLabel(credential.expires_at)}.</p>
        <button type="button" className="secondary" onClick={() => setCredential(undefined)}>Ocultar código</button>
      </div>}
    </details>}

    <details open={reference ? true : undefined}>
      <summary>Renovar referencia pública</summary>
      <p>Esta acción invalida el enlace público anterior.</p>
      {confirmRotation ? <button type="button" disabled={task.busy} onClick={() => void task.run(async () => {
        setReference((await custodyApi.rotate(custody.id)).public_reference);
        setConfirmRotation(false);
      })}>Confirmar nueva referencia</button>
        : <button type="button" className="secondary" disabled={task.busy} onClick={() => setConfirmRotation(true)}>
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

  const currentDetail = selected?.id === openId ? selected : undefined;
  const visible = items.filter((item) => !filter || item.state === filter);
  return <div className="dashboard-grid">
    <section aria-labelledby="mine-heading">
      <h2 id="mine-heading">Mis custodias</h2>
      <div className="actions"><button type="button" className="secondary" disabled={listTask.busy} onClick={load}>Actualizar custodias</button></div>
      <Field label="Filtrar por estado">
        <select value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="">Todos los estados</option>
          {Object.entries(stateLabel).map(([state, label]) => <option key={state} value={state}>{label}</option>)}
        </select>
      </Field>
      <Status {...listTask} />
      <ul className="items">{visible.map((item) => <li key={item.id}>
        <strong>{item.tracking_number}</strong><p>{stateLabel[item.state]}</p>
        <p>{item.description}</p>
        <button type="button" className="secondary" onClick={() => setOpenId(item.id)}>
          Ver detalle de {item.tracking_number}
        </button>
      </li>)}</ul>
      {!visible.length && !listTask.busy && !listTask.error && <p>Sin custodias para el estado elegido.</p>}
    </section>

    {verified ? <RegisterCustody points={points} onCreated={(item) => { update(item); setOpenId(item.id); }} />
      : <section><h2>Registrar un objeto</h2><p>Comprueba tu contacto para registrar custodias.</p></section>}

    {openId && <section className="full-width" aria-labelledby="detail-heading">
      <h2 id="detail-heading" tabIndex={-1}>Detalle privado</h2>
      <button type="button" className="secondary" onClick={() => setOpenId(null)}>Cerrar detalle</button>
      <Status {...detailTask} busy={!currentDetail && !detailTask.error} />
      {currentDetail && <>
        <CustodySummary custody={currentDetail} point={points.find((point) => point.id === currentDetail.point_id)} />
        <ParticipantActions key={currentDetail.id} custody={currentDetail} onUpdate={update} />
        <CustodyExceptions key={currentDetail.id} custody={currentDetail} />
      </>}
    </section>}
  </div>;
}
