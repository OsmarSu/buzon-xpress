import { useEffect, useState } from "react";

import type { User } from "../../services/auth";
import { custodyApi, type Point } from "../../services/custody";
import { Notifications } from "../custody/Notifications";
import { Participant } from "../custody/Participant";
import { Status, useTask } from "../shared/forms";

type Panel = "custodies" | "notices";

export function Dashboard({ user, initialCustody }: { user: User; initialCustody: string | null }) {
  const [points, setPoints] = useState<Point[]>([]);
  const [panel, setPanel] = useState<Panel>("custodies");
  const [custody, setCustody] = useState(initialCustody);
  const task = useTask();

  function loadPoints() {
    void task.run(async () => setPoints(await custodyApi.points()));
  }
  useEffect(loadPoints, []);

  return <>
    <nav aria-label="Áreas de trabajo" className="actions dashboard-nav">
      <button type="button" className={panel === "custodies" ? "" : "secondary"}
        aria-current={panel === "custodies" ? "page" : undefined} onClick={() => setPanel("custodies")}>Mis custodias</button>
      <button type="button" className={panel === "notices" ? "" : "secondary"}
        aria-current={panel === "notices" ? "page" : undefined} onClick={() => {
          setCustody(null);
          setPanel("notices");
        }}>Avisos</button>
    </nav>
    <Status {...task} />
    {task.error && <button type="button" className="secondary" onClick={loadPoints}>Volver a consultar los puntos</button>}
    {panel === "custodies" ? <Participant points={points} openId={custody} setOpenId={setCustody} verified={user.contact_verified} />
      : <Notifications onOpen={(id) => { setCustody(id); setPanel("custodies"); }} />}
  </>;
}
