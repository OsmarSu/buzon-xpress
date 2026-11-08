import { useEffect, useState } from "react";

import { custodyApi, dateLabel, type Notification } from "../../services/custody";
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
    <h2 id="notifications-heading">Avisos de mi cuenta</h2>
    <button type="button" className="secondary" onClick={load} disabled={task.busy}>Actualizar avisos</button>
    <Status {...task} />
    <ul className="items">{items.map((notice) => {
      const link = notice.body.match(custodyLink);
      return <li key={notice.id}>
        <strong>{notice.subject}</strong>
        <p>{notice.body.replace(custodyLink, "").trim()}</p>
        <p>{dateLabel(notice.created_at)} · {notice.read_at ? "Leído" : "Sin leer"}</p>
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
    {!items.length && !task.busy && !task.error && <p>Todavía no tienes avisos.</p>}
  </section>;
}
