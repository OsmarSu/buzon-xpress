import { useEffect, useId, useRef, useState, type ReactNode } from "react";

import { ApiError } from "../../services/api";
import { auth, isMfaChallenge, type MfaChallenge, type User } from "../../services/auth";
import { Dashboard } from "../dashboard/Dashboard";
import { Field, formData, Status, useTask, value } from "../shared/forms";

import { PublicHome } from "./PublicHome";
import { Brand, PublicHeader, SiteFooter } from "./SiteChrome";
import { MfaSecurity } from "./MfaSecurity";

import "./public.css";
import "./access.css";

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
  login: { title: "Iniciar sesión", detail: "Usa el correo y la contraseña de tu cuenta de BUZON Xpress.", submit: "Entrar" },
  register: { title: "Crear cuenta", detail: "Regístrate para gestionar tus objetos y consultar los que recibirás.", submit: "Crear mi cuenta" },
  "request-reset": {
    title: "Recuperar contraseña",
    detail: "Ingresa el correo que usas para acceder a tu cuenta.",
    submit: "Enviar solicitud",
  },
};

type AccessMode = "login" | "register" | "request-reset";

const accessStories = {
  login: {
    eyebrow: "Cómo usar tu cuenta",
    title: "Todo empieza en tu cuenta.",
    detail: "Al entrar verás las herramientas de tu cuenta.",
    steps: [
      { title: "Identifícate", detail: "Ingresa el correo y la contraseña de tu cuenta de BUZON Xpress." },
      { title: "Elige un área de trabajo", detail: "Abre Mis custodias para registrar o consultar objetos y Avisos para revisar sus novedades." },
      { title: "Consulta antes de actuar", detail: "Abre un registro para ver su estado y las acciones disponibles. El sistema informa el resultado de cada solicitud." },
    ],
    link: paths["request-reset"],
    linkLabel: "Recuperar mi acceso",
  },
  register: {
    eyebrow: "Cómo crear tu cuenta",
    title: "Tu cuenta, paso a paso.",
    detail: "Este formulario crea una cuenta personal. Después podrás entrar a tu espacio privado.",
    steps: [
      { title: "Completa tus datos", detail: "Escribe tu nombre y un correo al que tengas acceso. El teléfono es opcional." },
      { title: "Elige una contraseña", detail: "Usa al menos 15 caracteres y repítela para confirmar. Esta será tu contraseña de BUZON Xpress." },
      { title: "Verifica tu correo y entra", detail: "Abre el enlace que recibirás por correo y confirma la verificación. Luego inicia sesión con los datos que registraste." },
    ],
    noteTitle: "Después del registro",
    note: "En Mi cuenta verás el estado de tu contacto y podrás activar la verificación en dos pasos desde Seguridad de mi cuenta. Administración asigna los roles del personal.",
    link: paths.login,
    linkLabel: "Ya tengo una cuenta",
  },
  "request-reset": {
    eyebrow: "Cómo recuperar tu acceso",
    title: "Vuelve a entrar a tu cuenta.",
    detail: "La recuperación permite cambiar la contraseña de una cuenta existente.",
    steps: [
      { title: "Indica tu correo", detail: "Usa la misma dirección que registraste en BUZON Xpress." },
      { title: "Revisa tu bandeja", detail: "Si hay una cuenta habilitada con ese correo, recibirás un enlace. Revisa también la carpeta de spam." },
      { title: "Cambia la contraseña", detail: "Abre el enlace, escribe una nueva contraseña de al menos 15 caracteres y vuelve a iniciar sesión." },
    ],
    noteTitle: "Si activaste la verificación en dos pasos",
    note: "Cambiar la contraseña mantiene esa protección. Para entrar necesitarás tu aplicación autenticadora o un código de recuperación.",
    link: paths.login,
    linkLabel: "Volver a iniciar sesión",
  },
} satisfies Record<AccessMode, {
  eyebrow: string; title: string; detail: string;
  steps: { title: string; detail: string }[];
  noteTitle?: string; note?: string; link: string; linkLabel: string;
}>;

function AccessStory({ mode }: { mode: AccessMode }) {
  const story = accessStories[mode];
  const note = "note" in story ? story : undefined;
  return <aside className="access-story" aria-labelledby="access-story-heading">
    <div className="access-story-copy">
      <p className="public-eyebrow">{story.eyebrow}</p>
      <h2 id="access-story-heading">{story.title}</h2>
      <p>{story.detail}</p>
    </div>
    <ol className="access-journey" aria-label={story.eyebrow + " en tres pasos"}>
      {story.steps.map((step, index) => <li key={step.title}>
        <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
        <div><h3>{step.title}</h3><p>{step.detail}</p></div>
      </li>)}
    </ol>
    <div className="access-story-bottom">
      {note && <p><strong>{note.noteTitle}</strong>{note.note}</p>}
      <a href={story.link}>{story.linkLabel} <span aria-hidden="true">→</span></a>
    </div>
  </aside>;
}

function PasswordField({ label, name, register = false, hint }: {
  label: string; name: string; register?: boolean; hint?: string;
}) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  return <div className="field">
    <label htmlFor={id}>{label}</label>
    <div className="access-password">
      <input id={id} name={name} type={visible ? "text" : "password"}
        autoComplete={register ? "new-password" : "current-password"} aria-describedby={hint}
        required minLength={register ? 15 : 1} maxLength={128} />
      <button type="button" className="access-password-toggle" aria-pressed={visible}
        aria-label={(visible ? "Ocultar " : "Mostrar ") + label.toLowerCase()}
        onClick={() => setVisible((show) => !show)}>{visible ? "Ocultar" : "Mostrar"}</button>
    </div>
  </div>;
}

function AccessSkeleton() {
  return <div className="access-skeleton" role="status" aria-label="Cargando formulario de acceso">
    <span className="access-skeleton-line" /><span className="access-skeleton-field" />
    <span className="access-skeleton-line" /><span className="access-skeleton-field" />
    <span className="access-skeleton-button" />
    <span className="access-screenreader">Cargando formulario…</span>
  </div>;
}

function AccountPage({ children, mode }: { children: ReactNode; mode?: AccessMode }) {
  return <div className="public-site">
    <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
    <PublicHeader focused />
    <main className={"public-layout public-task-page access-task-page " + (mode ? "access-split" : "access-utility")}
      id="contenido-principal" tabIndex={-1}>
      <div className="access-panel">{children}</div>
      {mode && <AccessStory mode={mode} />}
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
  const [challenge, setChallenge] = useState<MfaChallenge | null>(null);
  const [recoveryMode, setRecoveryMode] = useState(false);
  const [challengeExpired, setChallengeExpired] = useState(false);
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
      heading.current.focus({ preventScroll: true });
      window.scrollTo(0, 0);
    }
  }, [loading, page, reset, token, user]);

  useEffect(() => {
    setChallengeExpired(false);
    if (!challenge) return;
    const timeout = window.setTimeout(() => setChallengeExpired(true),
      Math.max(0, new Date(challenge.expires_at).getTime() - Date.now()));
    heading.current?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
    return () => window.clearTimeout(timeout);
  }, [challenge]);

  useEffect(() => {
    const title = reset ? "Cambiar contraseña"
      : token ? "Comprobar correo"
        : challenge ? "Verificación en dos pasos"
        : page === "home" ? "Custodia temporal"
          : page === "account" ? "Mi espacio de custodia"
            : accessCopy[page].title;
    document.title = title + " · BUZON Xpress";
  }, [page, reset, token, challenge]);

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
        <MfaSecurity key={"security-" + user.id} />
        <Dashboard key={user.id} user={user} initialCustody={pendingCustody} />
      </main>
      <SiteFooter />
    </div>;
  }

  const mode = page === "account" ? "login" : page;
  const access = accessCopy[mode];
  if (challenge) return <AccountPage mode="login">
    <section className="public-auth-card access-form-card" aria-labelledby="challenge-heading">
      <p className="public-eyebrow">Último paso</p>
      <div className="access-challenge-symbol" aria-hidden="true">✓</div>
      <h1 id="challenge-heading" ref={heading} tabIndex={-1}>Verifica que eres tú</h1>
      <p>{recoveryMode ? "Ingresa uno de los códigos de recuperación que guardaste al activar esta protección."
        : "Abre tu aplicación autenticadora e ingresa el código de seis dígitos de BUZON Xpress."}</p>
      {status}
      {challengeExpired ? <p className="access-expired" role="alert">Esta solicitud venció. Vuelve a ingresar tu correo y contraseña para obtener otra.</p>
        : <form key={recoveryMode ? "recovery" : "totp"} aria-busy={task.busy} onSubmit={(event) => {
          const data = formData(event);
          doTask(async () => {
            const session = await auth.verifyMfa(challenge.challenge_token, value(data, "code"));
            setChallenge(null);
            setRecoveryMode(false);
            setUser(session.user);
            replacePage("account");
            setMessage("Sesión iniciada con verificación en dos pasos.");
          });
        }}>
          <Field label={recoveryMode ? "Código de recuperación" : "Código de la aplicación"}>
            <input className={recoveryMode ? "" : "access-otp-input"} name="code" type="text"
              inputMode={recoveryMode ? "text" : "numeric"} autoComplete="one-time-code"
              required pattern={recoveryMode ? undefined : "[0-9]{6}"} minLength={recoveryMode ? 1 : 6}
              maxLength={recoveryMode ? 128 : 6} autoFocus aria-describedby="challenge-hint" />
          </Field>
          <small id="challenge-hint">{recoveryMode ? "Cada código de recuperación se puede usar una sola vez."
            : "Si el código cambia antes de enviarlo, usa el nuevo."}</small>
          <button type="submit" disabled={task.busy}>{task.busy && <span className="access-spinner" aria-hidden="true" />}Verificar y entrar</button>
        </form>}
      <div className="access-challenge-options">
        {!challengeExpired && <button type="button" className="access-text-button" disabled={task.busy} onClick={() => {
          setRecoveryMode((current) => !current);
          task.setError("");
          setMessage("");
        }}>{recoveryMode ? "Usar mi aplicación autenticadora" : "Usar un código de recuperación"}</button>}
        <button type="button" className="access-text-button" disabled={task.busy} onClick={() => {
          setChallenge(null);
          setRecoveryMode(false);
          task.setError("");
          setMessage("");
        }}>Volver a iniciar sesión</button>
      </div>
    </section>
  </AccountPage>;

  return <AccountPage mode={mode}>
    <section className="public-auth-card access-form-card" aria-labelledby="access-heading">
      <div className="access-form-intro">
        <p className="public-eyebrow">{mode === "register" ? "Empieza con BUZON Xpress" : mode === "login" ? "Bienvenido de nuevo" : "Recupera tu acceso"}</p>
        <h1 id="access-heading" tabIndex={-1} ref={heading}>{access.title}</h1>
        <p>{access.detail}</p>
      </div>
      {status}
      {loading ? <AccessSkeleton /> : <>
        <form key={mode} onSubmit={(event) => {
          const form = event.currentTarget;
          const data = formData(event);
          const email = value(data, "email");
          const password = String(data.get("password") ?? "");
          doTask(async () => {
            if (mode === "login") {
              const session = await auth.login({ email, password });
              form.reset();
              if (isMfaChallenge(session)) {
                setChallenge(session);
                setRecoveryMode(false);
                return;
              }
              setUser(session.user);
              replacePage("account");
              setMessage("Sesión iniciada.");
            } else if (mode === "register") {
              if (password !== data.get("confirmation")) {
                task.setError("Las contraseñas deben coincidir.");
                return;
              }
              const phone = value(data, "phone");
              await auth.register({
                email, password, full_name: value(data, "name"), ...(phone ? { phone } : {}),
              });
              form.reset();
              replacePage("login");
              setMessage("Cuenta creada. Abre el enlace que recibirás por correo y confirma la verificación. Después inicia sesión. Si necesitas ayuda, consulta al personal del punto.");
            } else {
              await auth.requestReset(email);
              form.reset();
              replacePage("login");
              setMessage("Si existe una cuenta habilitada, el servicio enviará instrucciones a ese correo.");
            }
          });
        }} aria-busy={task.busy}>
          {mode === "register" && <div className="access-registration-fields">
            <Field label="Nombre completo"><input name="name" autoComplete="name" required maxLength={160} placeholder="Tu nombre y apellido" /></Field>
            <Field label="Teléfono (opcional)"><input name="phone" type="tel" autoComplete="tel" maxLength={24} placeholder="Número de contacto" /></Field>
          </div>}
          <Field label="Correo electrónico">
            <input name="email" type="email" autoComplete={mode === "register" ? "email" : "username"} required
              maxLength={254} placeholder="nombre@correo.com" />
          </Field>
          {mode !== "request-reset" && <>
            <PasswordField label="Contraseña" name="password" register={mode === "register"}
              hint={mode === "register" ? "password-hint" : undefined} />
            {mode === "register" && <>
              <small id="password-hint">Usa una frase de al menos 15 caracteres que solo tú conozcas.</small>
              <PasswordField label="Repetir contraseña" name="confirmation" register />
            </>}
          </>}
          {mode === "register" && <p className="access-form-note">Al registrarte obtendrás una cuenta personal. Verifica tu correo para habilitar el registro de objetos. Administración asigna los roles del personal.</p>}
          <button type="submit" disabled={task.busy}>
            {task.busy && <span className="access-spinner" aria-hidden="true" />}
            {task.busy ? "Procesando…" : access.submit}
            {!task.busy && <span aria-hidden="true">→</span>}
          </button>
        </form>
        <nav aria-label="Opciones de acceso" className="public-account-actions access-account-actions">
          {mode === "login" ? <>
            <p>¿Primera vez aquí? <a href={paths.register}>Crear cuenta</a></p>
            <a href={paths["request-reset"]}>Olvidé mi contraseña</a>
          </> : <p>¿Ya tienes cuenta? <a href={paths.login}>Iniciar sesión</a></p>}
        </nav>
        {mode === "login" && <div className="access-security-note">
          <span aria-hidden="true">✦</span>
          <p>Activa la verificación en dos pasos desde <strong>Seguridad de mi cuenta</strong> para proteger tus próximos accesos.</p>
        </div>}
      </>}
      <a className="public-return-link" href="/">← Volver al inicio</a>
    </section>
  </AccountPage>;
}
