import { useEffect, useRef, useState } from "react";

import type { Role, User } from "../../services/auth";
import { custodyApi, type Point } from "../../services/custody";
import { Notifications } from "../custody/Notifications";
import { Participant } from "../custody/Participant";
import { ReviewExceptions } from "../operations/Exceptions";
import { Operations } from "../operations/Operations";
import { Status, useTask } from "../shared/forms";
import { Administration, Audit } from "../supervision/Supervision";
import { WorkspaceGlyph, type WorkspaceIcon } from "./Workspace";
import "./workspace.css";

type Panel = "custodies" | "notices" | "operations" | "review" | "admin" | "audit";

const panels: Record<Panel, {
  label: string; title: string; description: string; icon: WorkspaceIcon;
}> = {
  custodies: {
    label: "Mis custodias", title: "Tus envíos y retiros", icon: "box",
    description: "Registra un objeto para otra persona o consulta el siguiente paso de una custodia existente.",
  },
  notices: {
    label: "Avisos", title: "Actualizaciones de tus custodias", icon: "notice",
    description: "Revisa recepciones, plazos y retiros desde una sola bandeja.",
  },
  operations: {
    label: "Terminal de operación", title: "Atención del punto", icon: "operation",
    description: "Elige el punto donde estás atendiendo. Luego localiza la custodia para recibir, verificar o confirmar.",
  },
  review: {
    label: "Resolver incidencias", title: "Incidencias y recuperaciones", icon: "incident",
    description: "Consulta el expediente y su evidencia antes de registrar una resolución o decidir una solicitud.",
  },
  admin: {
    label: "Administración", title: "Configuración del servicio", icon: "settings",
    description: "Mantén al día los puntos, sus ubicaciones, el personal autorizado y las versiones de tarifa.",
  },
  audit: {
    label: "Auditoría e indicadores", title: "Supervisión del punto", icon: "audit",
    description: "Selecciona un punto para consultar su historial. Define el periodo para obtener indicadores comparables.",
  },
};

const roles: Record<Role, string> = {
  USUARIO: "Cuenta personal", OPERADOR: "Operador del punto",
  ADMIN: "Administración", AUDITOR: "Auditoría",
};

const defaultPanel: Record<Role, Panel> = {
  USUARIO: "custodies", OPERADOR: "operations", ADMIN: "admin", AUDITOR: "audit",
};

const groups: { label: string; panels: Panel[]; roles?: Role[] }[] = [
  { label: "Mi actividad", panels: ["custodies", "notices"] },
  { label: "Atención", panels: ["operations"], roles: ["OPERADOR"] },
  { label: "Gestión del servicio", panels: ["review", "admin"], roles: ["ADMIN"] },
  { label: "Supervisión", panels: ["audit"], roles: ["ADMIN", "AUDITOR"] },
];

export function Dashboard({ user, initialCustody }: { user: User; initialCustody: string | null }) {
  const [points, setPoints] = useState<Point[]>([]);
  const [panel, setPanel] = useState<Panel>(initialCustody ? "custodies" : defaultPanel[user.role]);
  const [custody, setCustody] = useState(initialCustody);
  const task = useTask();
  const heading = useRef<HTMLHeadingElement>(null);
  const focusPanel = useRef(false);

  function loadPoints() {
    void task.run(async () => setPoints(await custodyApi.points()));
  }
  useEffect(loadPoints, []);

  useEffect(() => {
    if (focusPanel.current) {
      heading.current?.focus();
      focusPanel.current = false;
    }
  }, [panel]);

  function selectPanel(next: Panel) {
    if (panel === next) return;
    if (next === "notices" || next === "operations" || next === "review") setCustody(null);
    focusPanel.current = true;
    setPanel(next);
  }

  function openCustody(id: string) {
    focusPanel.current = false;
    setCustody(id);
    setPanel("custodies");
  }

  const current = panels[panel];
  return <div className="workspace">
    <aside className="workspace-sidebar">
      <div className="workspace-sidebar-title">
        <span className="workspace-sidebar-mark"><WorkspaceGlyph name="box" /></span>
        <div><strong>Espacio de trabajo</strong><span>{roles[user.role]}</span></div>
      </div>
      <nav aria-label="Áreas de trabajo" className="workspace-nav">
        {groups.filter((group) => !group.roles || group.roles.includes(user.role)).map((group) => (
          <div className="workspace-nav-group" key={group.label}>
            <p>{group.label}</p>
            <ul>{group.panels.map((key) => <li key={key}>
              <button type="button" className="workspace-nav-button" aria-current={panel === key ? "page" : undefined}
                onClick={() => selectPanel(key)}>
                <WorkspaceGlyph name={panels[key].icon} />
                <span>{panels[key].label}</span>
                <WorkspaceGlyph name="chevron" className="workspace-nav-indicator" />
              </button>
            </li>)}</ul>
          </div>
        ))}
      </nav>
    </aside>

    <div className="workspace-content">
      <header className="workspace-hero">
        <div className="workspace-hero-copy">
          <p className="workspace-eyebrow">{current.label}</p>
          <h2 ref={heading} tabIndex={-1}>{current.title}</h2>
          <p>{current.description}</p>
        </div>
        <span className="workspace-hero-icon"><WorkspaceGlyph name={current.icon} /></span>
      </header>
      {(task.error || task.busy) && <div className="workspace-feedback">
        <Status {...task} />
        {task.error && <button type="button" className="secondary" onClick={loadPoints}>Volver a consultar los puntos</button>}
      </div>}
      {panel === "custodies" ? <Participant points={points} openId={custody} setOpenId={setCustody} verified={user.contact_verified} />
        : panel === "notices" ? <Notifications onOpen={openCustody} />
        : panel === "operations" ? <Operations points={points} />
        : panel === "review" ? <ReviewExceptions actorId={user.id} />
        : panel === "admin" ? <Administration points={points} onPointChange={loadPoints} /> : <Audit points={points} />}
    </div>
  </div>;
}
