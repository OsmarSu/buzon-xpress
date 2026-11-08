import { useState } from "react";

import { custodyPath, dateLabel, type Authorization, type Custody, type Handover } from "../../services/custody";
import { Field, formData, Status, useMutation, useTask, value } from "../shared/forms";

export function Receipt({ handover }: { handover: Handover }) {
  return <div className="receipt" role="status">
    <strong>{handover.kind === "DEVOLUCION" ? "Devolución registrada" : "Retiro registrado"}</strong>
    <p>Comprobante <code>{handover.id}</code></p>
    <p>Confirmado {dateLabel(handover.confirmed_at)} · Operador <code>{handover.operator_id}</code></p>
  </div>;
}

export function AuthorizedHandover({ authorization, kind, onConfirmed, onAborted }: {
  authorization: Authorization;
  kind: "RETIRO" | "DEVOLUCION";
  onConfirmed: (handover: Handover) => void;
  onAborted?: (custody: Custody) => void;
}) {
  const task = useTask();
  const confirm = useMutation();
  const abort = useMutation();
  const [pending, setPending] = useState(false);
  const [delivered, setDelivered] = useState(false);
  const isReturn = kind === "DEVOLUCION";

  return <div className="receipt">
    <h3>Autorizado para {isReturn ? "devolver" : "entregar"}</h3>
    <dl className="details">
      <div><dt>Autorización</dt><dd><code>{authorization.authorization_id}</code></dd></div>
      <div><dt>Objeto</dt><dd>{authorization.description}</dd></div>
      <div><dt>Ubicación interna</dt><dd>{authorization.location_code}</dd></div>
      <div><dt>Vence</dt><dd>{dateLabel(authorization.expires_at)}</dd></div>
    </dl>
    {pending && <p role="alert" className="warning">
      Confirmación pendiente. No repitas la entrega física. Reintenta solo el registro con esta autorización.
    </p>}
    <form onSubmit={(event) => {
      event.preventDefault();
      void task.run(async () => {
        setPending(true);
        const result = await confirm<Handover>(custodyPath(authorization.custody_id, isReturn ? "return-handover" : "handover"), {
          authorization_id: authorization.authorization_id,
          expected_version: authorization.version,
          physically_delivered: true,
        });
        setPending(false);
        onConfirmed(result);
      });
    }} aria-busy={task.busy}>
      <label className="check">
        <input type="checkbox" required checked={delivered} disabled={pending || task.busy}
          onChange={(event) => setDelivered(event.target.checked)} />
        {isReturn ? "Confirmo que ya devolví físicamente el objeto al emisor" : "Confirmo que ya entregué físicamente el objeto"}
      </label>
      <button type="submit" disabled={task.busy || !delivered}>{pending ? "Reintentar solo el registro"
        : isReturn ? "Registrar devolución realizada" : "Registrar entrega realizada"}</button>
    </form>
    {!pending && !delivered && onAborted && <details>
      <summary>No entregado · anular preparación</summary>
      <form onSubmit={(event) => {
        const data = formData(event);
        void task.run(async () => onAborted(await abort<Custody>(custodyPath(authorization.custody_id, "abort-handover"), {
          authorization_id: authorization.authorization_id, physically_delivered: false, reason: value(data, "reason"),
        })));
      }}>
        <Field label="Motivo de anulación"><textarea name="reason" required maxLength={500} /></Field>
        <button type="submit" className="secondary" disabled={task.busy}>Anular porque no se entregó</button>
      </form>
    </details>}
    <Status {...task} />
  </div>;
}
