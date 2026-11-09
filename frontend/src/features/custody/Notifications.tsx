import { useEffect, useState } from "react";

import { custodyApi, dateLabel, type Notification } from "../../services/custody";
import { WorkspaceBadge, WorkspaceEmpty, WorkspaceGlyph, WorkspaceHeading } from "../dashboard/Workspace";
import { Status, useTask } from "../shared/forms";

const custodyLink = /\/#custodia=([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})/i;

export function Notifications({ onOpen }: { onOpen: (id: string) => void }) {
  const task = useTask();
  const [items, setItems] = useState<Notification[]>([]);

  function load() {
    void task.run(async () => setItems(await custodyApi.notifications()));
  }
  useEffect(load, []);

  return <section aria-labelledby="notifications-heading">
    <WorkspaceHeading id="notifications-heading" title="Avisos de mi cuenta"
      description="Abre el detalle relacionado o marca un aviso como leído."
      action={<button type="button" className="secondary workspace-quiet-action" onClick={load} disabled={task.busy}>
        <WorkspaceGlyph name="refresh" /> Actualizar avisos
      </button>} />
    <Status {...task} />
    <ul className="items workspace-records">{items.map((notice) => {
      const link = notice.body.match(custodyLink);
      return <li key={notice.id}>
        <div className="workspace-record-top">
          <strong>{notice.subject}</strong>
          <WorkspaceBadge tone={notice.read_at ? "neutral" : "info"}>{notice.read_at ? "Leído" : "Sin leer"}</WorkspaceBadge>
        </div>
        <p className="workspace-meta">{dateLabel(notice.created_at)}</p>
        <p>{notice.body.replace(custodyLink, "").trim()}</p>
        <div className="actions">
          {link && <button type="button" className="secondary" onClick={() => onOpen(link[1])}>Abrir custodia</button>}
          {!notice.read_at && <button type="button" disabled={task.busy}
            onClick={() => void task.run(async () => {
              await custodyApi.markRead(notice.id);
              setItems(await custodyApi.notifications());
            })}>Marcar como leído</button>}
        </div>
      </li>;
    })}</ul>
    {!items.length && !task.busy && !task.error && <WorkspaceEmpty icon="notice" title="Todavía no tienes avisos"
      description="Las novedades de tus custodias aparecerán aquí." />}
  </section>;
}
