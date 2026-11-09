import { useState } from "react";

import { request as apiRequest } from "../../services/api";
import { custodyPath, type Authorization, type Custody, type Handover } from "../../services/custody";
import { WorkspaceBadge, WorkspaceHeading } from "../dashboard/Workspace";
import { Field, formData, Status, useMutation, useTask, value } from "../shared/forms";
import { AuthorizedHandover, Receipt } from "./Handover";

interface Incident {
  id: string;
  custody_id: string;
  state: "ABIERTA" | "EN_REVISION" | "RESUELTA";
  is_blocking: boolean;
}

interface Recovery {
  id: string;
  custody_id: string;
  state: "PENDIENTE" | "APROBADA" | "RECHAZADA" | "EJECUTADA";
}

const incidentState: Record<Incident["state"], string> = {
  ABIERTA: "Abierta", EN_REVISION: "En revisión", RESUELTA: "Resuelta",
};

const recoveryState: Record<Recovery["state"], string> = {
  PENDIENTE: "Pendiente", APROBADA: "Aprobada", RECHAZADA: "Rechazada", EJECUTADA: "Ejecutada",
};

const reasons = {
  REEMITIR_CREDENCIAL: "Reemisión asistida de credencial",
  CAMBIAR_DESTINATARIO: "Cambio de destinatario",
  AUTORIZAR_DEVOLUCION: "Autorizar devolución al emisor",
  RECONCILIAR_ENTREGA: "Conciliar entrega realizada",
};

export function CustodyExceptions({ custody }: { custody: Custody }) {
  const incidentTask = useTask();
  const recoveryTask = useTask();
  const report = useMutation();
  const request = useMutation();
  const [incident, setIncident] = useState<Incident>();
  const [recovery, setRecovery] = useState<Recovery>();
  const [purpose, setPurpose] = useState<keyof typeof reasons>("REEMITIR_CREDENCIAL");

  return <>
    <details className="workspace-action-group">
      <summary>Registrar una incidencia</summary>
      <p>Describe la diferencia observada sin incluir el código ni datos personales de terceros.</p>
      <form onSubmit={(event) => {
        const form = event.currentTarget;
        const data = formData(event);
        void incidentTask.run(async () => {
          setIncident(await report<Incident>(custodyPath(custody.id, "incidents"), {
            kind: value(data, "kind"),
            description: value(data, "description"),
            is_blocking: data.has("blocking"),
          }));
          form.reset();
        });
      }}>
        <Field label="Tipo de incidencia"><input name="kind" maxLength={40} required /></Field>
        <Field label="Hechos observados"><textarea name="description" maxLength={1000} required /></Field>
        <label className="check"><input type="checkbox" name="blocking" /> Señalar posible impedimento de entrega</label>
        <button type="submit" disabled={incidentTask.busy}>Registrar incidencia</button>
      </form>
      <Status {...incidentTask} />
      {incident && <p role="status" className="receipt">Incidencia <code>{incident.id}</code> · {incidentState[incident.state]}
        {incident.is_blocking ? " · entrega bloqueada" : ""}</p>}
    </details>

    <details className="workspace-action-group">
      <summary>Solicitar recuperación asistida</summary>
      <p>La solicitud queda pendiente hasta que una segunda persona autorizada revise la evidencia.</p>
      <form onSubmit={(event) => {
        const form = event.currentTarget;
        const data = formData(event);
        const replacement = value(data, "recipient");
        void recoveryTask.run(async () => {
          setRecovery(await request<Recovery>("/recovery-requests", {
            custody_id: custody.id,
            purpose,
            evidence: value(data, "evidence"),
            ...(replacement && purpose === "CAMBIAR_DESTINATARIO" ? { target_recipient_id: replacement } : {}),
          }));
          form.reset();
        });
      }}>
        <Field label="Propósito">
          <select value={purpose} disabled={recoveryTask.busy}
            onChange={(event) => setPurpose(event.target.value as keyof typeof reasons)}>
            {Object.entries(reasons).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </Field>
        {purpose === "CAMBIAR_DESTINATARIO" && <Field label="Identificador autorizado del nuevo destinatario">
          <input name="recipient" required maxLength={36} />
        </Field>}
        <Field label="Evidencia y fundamento"><textarea name="evidence" maxLength={1000} required /></Field>
        <button type="submit" disabled={recoveryTask.busy}>Crear solicitud</button>
      </form>
      <Status {...recoveryTask} />
      {recovery && <p role="status" className="receipt">Solicitud <code>{recovery.id}</code> · {recoveryState[recovery.state]}</p>}
    </details>
  </>;
}

export function Returns({ custody, onAuthorized, onReturned }: {
  custody: Custody; onAuthorized: (result: Authorization) => void; onReturned: () => void;
}) {
  const task = useTask();
  const send = useMutation();
  const [authorization, setAuthorization] = useState<Authorization>();
  const [handover, setHandover] = useState<Handover>();

  if (handover) return <Receipt handover={handover} />;
  if (authorization) return <AuthorizedHandover authorization={authorization} kind="DEVOLUCION"
    onConfirmed={(result) => {
      setAuthorization(undefined);
      setHandover(result);
      onReturned();
    }} />;
  if (custody.state === "DEVOLUCION_EN_CURSO") {
    return <p className="warning">Hay una devolución preparada. Si ya ocurrió, abre conciliación y conserva la evidencia.</p>;
  }
  if (custody.state !== "EN_CUSTODIA") return null;
  return <details className="workspace-action-group">
    <summary>Preparar devolución aprobada</summary>
    <p>Comprueba visualmente al emisor antes de preparar la devolución.</p>
    <form onSubmit={(event) => {
      const data = formData(event);
      void task.run(async () => {
        const result = await send<Authorization>(custodyPath(custody.id, "return-authorization"), {
          recovery_request_id: value(data, "recovery"),
          expected_version: custody.version,
          sender_check: "COMPROBACION_VISUAL_COMPLETADA",
        });
        setAuthorization(result);
        onAuthorized(result);
      });
    }}>
      <Field label="Identificador de solicitud aprobada"><input name="recovery" required maxLength={36} /></Field>
      <label className="check"><input type="checkbox" required /> Comprobación visual del emisor completada</label>
      <button type="submit" disabled={task.busy}>Preparar devolución</button>
    </form>
    <Status {...task} />
  </details>;
}

interface IncidentDetail extends Incident {
  kind: string;
  description: string;
  opened_by: string;
  resolved_by?: string | null;
  resolution_note?: string | null;
}

interface RecoveryDetail extends Recovery {
  purpose: keyof typeof reasons;
  evidence: string;
  requested_by: string;
  decided_by?: string | null;
  decision_note?: string | null;
}

function ResolveIncident() {
  const task = useTask();
  const send = useMutation();
  const [id, setId] = useState("");
  const [item, setItem] = useState<IncidentDetail>();
  const endpoint = "/incidents/" + encodeURIComponent(id.trim());

  return <section aria-labelledby="resolve-heading">
    <WorkspaceHeading id="resolve-heading" title="Resolver incidencia"
      description="Consulta el registro y comprueba qué ocurrió antes de guardar una resolución." />
    <form onSubmit={(event) => {
      event.preventDefault();
      void task.run(async () => setItem(await apiRequest<IncidentDetail>(endpoint)));
    }}>
      <Field label="Identificador de incidencia"><input required maxLength={36} value={id} disabled={task.busy}
        onChange={(event) => { setId(event.target.value); setItem(undefined); }} /></Field>
      <button type="submit" className="secondary" disabled={task.busy}>Consultar incidencia</button>
    </form>
    {item && <div className="receipt">
      <div className="workspace-record-top"><strong>{item.kind}</strong>
        <WorkspaceBadge tone={item.state === "RESUELTA" ? "good" : "pending"}>{incidentState[item.state]}</WorkspaceBadge>
      </div>
      <p>{item.description}</p>
      <p>Abierta por <code>{item.opened_by}</code></p>
      <p>Custodia <code>{item.custody_id}</code> · {item.is_blocking ? "Bloqueante" : "Sin bloqueo"}</p>
      {item.resolution_note && <p>Resolución registrada: {item.resolution_note}</p>}
    </div>}
    {item && item.state !== "RESUELTA" && <form onSubmit={(event) => {
      const reason = value(formData(event), "reason");
      void task.run(async () => {
        const result = await send<Incident>(endpoint + "/resolve", { reason });
        setItem({ ...item, ...result, resolution_note: reason });
      });
    }}>
      <Field label="Fundamento de la resolución"><textarea name="reason" required maxLength={1000} /></Field>
      <label className="check workspace-confirmation"><input type="checkbox" required /> Comprobé el inventario y la diferencia</label>
      <button type="submit" disabled={task.busy}>Resolver incidencia</button>
    </form>}
    <Status {...task} />
  </section>;
}

function DecideRecovery({ actorId }: { actorId: string }) {
  const task = useTask();
  const send = useMutation();
  const [id, setId] = useState("");
  const [item, setItem] = useState<RecoveryDetail>();
  const endpoint = "/recovery-requests/" + encodeURIComponent(id.trim());
  const isOwn = item?.requested_by === actorId;

  return <section aria-labelledby="decision-heading">
    <WorkspaceHeading id="decision-heading" title="Revisar solicitud de recuperación"
      description="Abre el expediente y verifica que otra persona autorizada haya iniciado la solicitud." />
    <form onSubmit={(event) => {
      event.preventDefault();
      void task.run(async () => setItem(await apiRequest<RecoveryDetail>(endpoint)));
    }}>
      <Field label="Identificador de solicitud"><input required maxLength={36} value={id} disabled={task.busy}
        onChange={(event) => { setId(event.target.value); setItem(undefined); }} /></Field>
      <button type="submit" className="secondary" disabled={task.busy}>Consultar expediente</button>
    </form>
    {item && <div className="receipt">
      <div className="workspace-record-top"><strong>{reasons[item.purpose]}</strong>
        <WorkspaceBadge tone={item.state === "PENDIENTE" ? "pending" : "neutral"}>{recoveryState[item.state]}</WorkspaceBadge>
      </div>
      <p>{item.evidence}</p>
      <p>Solicitó <code>{item.requested_by}</code></p>
      <p>Custodia <code>{item.custody_id}</code></p>
      {item.decision_note && <p>Decisión registrada: {item.decision_note}</p>}
    </div>}
    {item?.state === "PENDIENTE" && isOwn && <p className="warning">La revisión corresponde a otra persona autorizada.</p>}
    {item?.state === "PENDIENTE" && !isOwn && <form onSubmit={(event) => {
      const data = formData(event);
      const note = value(data, "note");
      void task.run(async () => {
        const result = await send<Recovery>(endpoint + "/decision", { decision: value(data, "decision"), note });
        setItem({ ...item, ...result, decision_note: note });
      });
    }}>
      <Field label="Decisión">
        <select name="decision" required defaultValue="">
          <option value="">Elige una decisión</option><option value="APROBAR">Aprobar</option><option value="RECHAZAR">Rechazar</option>
        </select>
      </Field>
      <Field label="Justificación de la decisión"><textarea name="note" required maxLength={1000} /></Field>
      <label className="check workspace-confirmation"><input type="checkbox" required /> Revisé la evidencia del expediente</label>
      <button type="submit" disabled={task.busy}>Registrar decisión</button>
    </form>}
    <Status {...task} />
  </section>;
}

export function ReviewExceptions({ actorId }: { actorId: string }) {
  return <div className="dashboard-grid"><ResolveIncident /><DecideRecovery actorId={actorId} /></div>;
}
