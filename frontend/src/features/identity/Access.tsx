import { useEffect, useRef, useState, type ReactNode } from "react";

import { ApiError } from "../../services/api";
import { auth, type User } from "../../services/auth";
import { Dashboard } from "../dashboard/Dashboard";
import { Field, formData, Status, useTask, value } from "../shared/forms";

import { PublicHome } from "./PublicHome";
import { Brand, PublicHeader, SiteFooter } from "./SiteChrome";

import "./public.css";

const paths = {
  home: "/",
  login: "/acceso",
  register: "/registro",
  "request-reset": "/recuperar",
  account: "/cuenta",
} as const;

type Page = keyof typeof paths;

function pageFromPath(): Page {
  const pathname = location.pathname.replace(/\/$/, "") || "/";
  return (Object.keys(paths) as Page[]).find((page) => paths[page] === pathname) ?? "home";
}

interface Links {
  verificationToken: string | null;
  resetToken: string | null;
  initialReference: string | null;
  initialCustody: string | null;
}

const roleLabels = {
  ADMIN: "Administración",
  AUDITOR: "Auditoría",
  OPERADOR: "Operación del punto",
  USUARIO: "Cuenta personal",
};

const accessCopy = {
  login: { title: "Iniciar sesión", detail: "Ingresa a tu cuenta para registrar y consultar custodias.", submit: "Entrar" },
  register: { title: "Crear cuenta general", detail: "Comprueba tu contacto después de registrar tu cuenta.", submit: "Registrar cuenta" },
  "request-reset": {
    title: "Recuperar contraseña",
    detail: "Ingresa el correo que usas para acceder a tu cuenta.",
    submit: "Enviar solicitud",
  },
};

function AccountPage({ children }: { children: ReactNode }) {
  return <div className="public-site">
    <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
    <PublicHeader focused />
    <main className="public-layout public-task-page" id="contenido-principal" tabIndex={-1}>
      {children}
    </main>
    <SiteFooter />
  </div>;
}

export function Access({ verificationToken, resetToken, initialReference, initialCustody }: Links) {
  const [user, setUser] = useState<User | null>(null);
  const [page, setPage] = useState<Page>(() => initialCustody ? "account" : pageFromPath());
  const [pendingCustody, setPendingCustody] = useState(initialCustody);
  const [token, setToken] = useState(verificationToken);
  const [reset, setReset] = useState(resetToken);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const heading = useRef<HTMLHeadingElement>(null);
  const shouldMoveFocus = useRef(Boolean(resetToken || verificationToken));
  const task = useTask();

  useEffect(() => {
    void task.run(async () => {
      try {
        setUser(await auth.me());
        if (!verificationToken && !resetToken && page !== "home" && location.pathname !== paths.account) {
          replacePage("account");
        }
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 401)) throw error;
        if (!verificationToken && !resetToken && page === "account") replacePage("login");
      } finally {
        setLoading(false);
      }
    });
  }, []);

  useEffect(() => {
    if (!loading && shouldMoveFocus.current && heading.current) {
      shouldMoveFocus.current = false;
      heading.current.focus();
    }
  }, [loading, page, reset, token, user]);

  useEffect(() => {
    const title = reset ? "Cambiar contraseña"
      : token ? "Comprobar correo"
        : page === "home" ? "Custodia temporal"
          : page === "account" ? "Mi espacio de custodia"
            : accessCopy[page].title;
    document.title = title + " · BUZON Xpress";
  }, [page, reset, token]);

  function replacePage(next: Page) {
    if (location.pathname !== paths[next] || location.search || location.hash) {
      history.replaceState(null, "", paths[next]);
    }
    shouldMoveFocus.current = true;
    setPage(next);
  }

  function doTask(action: () => Promise<void>) {
    setMessage("");
    void task.run(action);
  }

  const status = <Status busy={task.busy || loading} error={task.error} message={message} />;

  if (reset) {
    return <AccountPage>
      <section className="public-auth-card" aria-labelledby="reset-heading">
        <p className="public-eyebrow">Recuperación de cuenta</p>
        <h1 id="reset-heading" tabIndex={-1} ref={heading}>Cambiar contraseña</h1>
        <p>Elige una contraseña de al menos 15 caracteres y escríbela dos veces.</p>
        {status}
        {!loading && <form aria-busy={task.busy} onSubmit={(event) => {
          const form = event.currentTarget;
          const data = formData(event);
          const password = String(data.get("password"));
          doTask(async () => {
            if (password !== data.get("confirmation")) {
              task.setError("Las contraseñas deben coincidir.");
              return;
            }
            await auth.completeReset(reset, password);
            form.reset();
            setReset(null);
            setUser(null);
            replacePage("login");
            setMessage("Contraseña actualizada. Inicia sesión con tu nueva contraseña.");
          });
        }}>
          <Field label="Nueva contraseña">
            <input name="password" type="password" required minLength={15} maxLength={128} autoComplete="new-password" />
          </Field>
          <Field label="Repetir nueva contraseña">
            <input name="confirmation" type="password" required minLength={15} maxLength={128} autoComplete="new-password" />
          </Field>
          <button type="submit" disabled={task.busy}>Cambiar contraseña</button>
        </form>}
        <a className="public-return-link" href="/">Volver al inicio</a>
      </section>
    </AccountPage>;
  }

  if (token) {
    return <AccountPage>
      <section className="public-auth-card public-verify-card" aria-labelledby="verify-heading">
        <p className="public-eyebrow">Comprobación de contacto</p>
        <h1 id="verify-heading" tabIndex={-1} ref={heading}>Comprobar correo</h1>
        <p>Confirma que tienes acceso al correo asociado a tu cuenta.</p>
        {status}
        {!loading && <button type="button" disabled={task.busy} onClick={() => doTask(async () => {
          await auth.verifyContact(token);
          if (user) setUser(await auth.me());
          setToken(null);
          replacePage(user ? "account" : "login");
          setMessage("Correo comprobado.");
        })}>Confirmar correo</button>}
        <a className="public-return-link" href="/">Volver al inicio</a>
      </section>
    </AccountPage>;
  }

  if (page === "home") return <PublicHome signedIn={Boolean(user)} initialReference={initialReference} />;

  if (user && page === "account" && !loading) {
    return <div className="workspace-shell">
      <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
      <header className="workspace-topbar">
        <div className="workspace-topbar-inner">
          <a className="public-brand-link" href="/" aria-label="BUZON Xpress, inicio"><Brand /></a>
          <span className="workspace-role">{roleLabels[user.role]}</span>
        </div>
      </header>
      <main className="shell workspace-main" id="contenido-principal" tabIndex={-1}>
        <div className="workspace-overview">
          <div className="workspace-title">
            <p className="public-eyebrow">Espacio privado</p>
            <h1 tabIndex={-1} ref={heading}>Mi espacio de custodia</h1>
            <p>Consulta tus operaciones y el estado informado por el punto.</p>
          </div>
          <section className="workspace-account" aria-labelledby="account-heading">
            <div>
              <h2 id="account-heading">Mi cuenta</h2>
              <p className="workspace-name">{user.full_name}</p>
              <p className="workspace-contact">{user.contact_verified ? "Contacto comprobado" : "Contacto pendiente"}</p>
            </div>
            <button type="button" className="secondary" disabled={task.busy} onClick={() => doTask(async () => {
              try {
                await auth.logout();
              } catch (error) {
                if (!(error instanceof ApiError && error.status === 401)) throw error;
              }
              setUser(null);
              setPendingCustody(null);
              replacePage("login");
              setMessage("Sesión cerrada.");
            })}>Cerrar sesión</button>
            <details>
              <summary>Identificador de mi cuenta</summary>
              <p>Compártelo con personal autorizado para comprobar tu contacto o asignarte funciones.</p>
              <p><code>{user.id}</code></p>
            </details>
          </section>
        </div>
        {status}
        <Dashboard key={user.id} user={user} initialCustody={pendingCustody} />
      </main>
      <SiteFooter />
    </div>;
  }

  const mode = page === "account" ? "login" : page;
  const access = accessCopy[mode];
  return <AccountPage>
    <section className="public-auth-card" aria-labelledby="access-heading">
      <p className="public-eyebrow">Mi cuenta</p>
      <h1 id="access-heading" tabIndex={-1} ref={heading}>{access.title}</h1>
      <p>{access.detail}</p>
      {status}
      {!loading && <>
        <form key={mode} onSubmit={(event) => {
          const form = event.currentTarget;
          const data = formData(event);
          const email = value(data, "email");
          const password = String(data.get("password") ?? "");
          doTask(async () => {
            if (mode === "login") {
              const session = await auth.login({ email, password });
              setUser(session.user);
              replacePage("account");
              setMessage("Sesión iniciada.");
            } else if (mode === "register") {
              const phone = value(data, "phone");
              await auth.register({
                email, password, full_name: value(data, "name"), ...(phone ? { phone } : {}),
              });
              replacePage("login");
              setMessage("Cuenta registrada. Comprueba tu contacto por correo o con el personal del punto.");
            } else {
              await auth.requestReset(email);
              replacePage("login");
              setMessage("Si existe una cuenta habilitada, el servicio enviará instrucciones a ese correo.");
            }
            form.reset();
          });
        }} aria-busy={task.busy}>
          {mode === "register" && <>
            <Field label="Nombre completo"><input name="name" autoComplete="name" required maxLength={160} /></Field>
            <Field label="Teléfono (opcional)"><input name="phone" type="tel" autoComplete="tel" maxLength={24} /></Field>
          </>}
          <Field label="Correo electrónico">
            <input name="email" type="email" autoComplete="username" required maxLength={254} />
          </Field>
          {mode !== "request-reset" && <>
            <Field label="Contraseña">
              <input name="password" type="password" autoComplete={mode === "register" ? "new-password" : "current-password"}
                aria-describedby={mode === "register" ? "password-hint" : undefined} required
                minLength={mode === "register" ? 15 : 1} maxLength={128} />
            </Field>
            {mode === "register" && <small id="password-hint">Usa al menos 15 caracteres.</small>}
          </>}
          <button type="submit" disabled={task.busy}>{access.submit}</button>
        </form>
        <nav aria-label="Opciones de acceso" className="public-account-actions">
          {mode === "login" ? <>
            <a href={paths.register}>Crear cuenta</a>
            <a href={paths["request-reset"]}>Recuperar contraseña</a>
          </> : <a href={paths.login}>Volver a iniciar sesión</a>}
        </nav>
      </>}
      <a className="public-return-link" href="/">Volver al inicio</a>
    </section>
  </AccountPage>;
}
