import { useState } from "react";

import { custodyPath, type Authorization, type Custody, type Handover } from "../../services/custody";
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
    <details>
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
      {incident && <p role="status" className="receipt">Incidencia <code>{incident.id}</code> · {incident.state}
        {incident.is_blocking ? " · entrega bloqueada" : ""}</p>}
    </details>

    <details>
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
      {recovery && <p role="status" className="receipt">Solicitud <code>{recovery.id}</code> · {recovery.state}</p>}
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
  return <details>
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

export function ReviewExceptions() {
  const incidenceTask = useTask();
  const decisionTask = useTask();
  const resolve = useMutation();
  const decide = useMutation();
  const [incident, setIncident] = useState<Incident>();
  const [recovery, setRecovery] = useState<Recovery>();

  return <div className="dashboard-grid">
    <section aria-labelledby="resolve-heading">
      <h2 id="resolve-heading">Resolver incidencia</h2>
      <p>Verifica el inventario y las circunstancias antes de resolver.</p>
      <form onSubmit={(event) => {
        const data = formData(event);
        const id = encodeURIComponent(value(data, "id"));
        void incidenceTask.run(async () =>
          setIncident(await resolve<Incident>("/incidents/" + id + "/resolve", { reason: value(data, "reason") })));
      }}>
        <Field label="Identificador de incidencia"><input name="id" required maxLength={36} /></Field>
        <Field label="Fundamento de la resolución"><textarea name="reason" required maxLength={1000} /></Field>
        <button type="submit" disabled={incidenceTask.busy}>Resolver incidencia</button>
      </form>
      <Status {...incidenceTask} />
      {incident && <p role="status" className="receipt">Incidencia <code>{incident.id}</code> · {incident.state}</p>}
    </section>
    <section aria-labelledby="decision-heading">
      <h2 id="decision-heading">Revisar solicitud de recuperación</h2>
      <p>Consulta la evidencia del expediente y verifica que otra persona haya solicitado la recuperación.</p>
      <form onSubmit={(event) => {
        const data = formData(event);
        const id = encodeURIComponent(value(data, "id"));
        void decisionTask.run(async () => setRecovery(await decide<Recovery>("/recovery-requests/" + id + "/decision", {
          decision: value(data, "decision"),
          note: value(data, "note"),
        })));
      }}>
        <Field label="Identificador de solicitud"><input name="id" required maxLength={36} /></Field>
        <Field label="Decisión">
          <select name="decision" required defaultValue="">
            <option value="">Elige una decisión</option><option value="APROBAR">Aprobar</option><option value="RECHAZAR">Rechazar</option>
          </select>
        </Field>
        <Field label="Justificación de la decisión"><textarea name="note" required maxLength={1000} /></Field>
        <label className="check"><input type="checkbox" required /> Revisé la evidencia del expediente</label>
        <button type="submit" disabled={decisionTask.busy}>Registrar decisión</button>
      </form>
      <Status {...decisionTask} />
      {recovery && <p role="status" className="receipt">Solicitud <code>{recovery.id}</code> · {recovery.state}</p>}
    </section>
  </div>;
}
