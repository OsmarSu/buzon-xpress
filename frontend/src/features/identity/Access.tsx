import { useEffect, useRef, useState } from "react";

import { ApiError } from "../../services/api";
import { auth, type User } from "../../services/auth";
import { PublicService } from "../custody/PublicService";
import { Dashboard } from "../dashboard/Dashboard";
import { Field, formData, Status, useTask, value } from "../shared/forms";

import "./public.css";

type Mode = "login" | "register" | "request-reset";

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

function Brand() {
  return <span className="buzon-wordmark">
    <span className="buzon-brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none">
        <path d="m5 11 11-6 11 6v12l-11 6-11-6V11Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        <path d="m5 11 11 6 11-6M16 17v12m-5-21 11 6" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
      </svg>
    </span>
    <span>BUZON <span className="buzon-wordmark-accent">Xpress</span></span>
  </span>;
}

function ServiceArt() {
  return <svg className="public-hero-art" viewBox="0 0 400 356" aria-hidden="true" focusable="false" fill="none">
    <defs>
      <linearGradient id="parcel-lid" x1="138" y1="103" x2="334" y2="211" gradientUnits="userSpaceOnUse">
        <stop stopColor="#eef4ff" /><stop offset="1" stopColor="#9fc3ff" />
      </linearGradient>
      <linearGradient id="parcel-front" x1="128" y1="155" x2="235" y2="289" gradientUnits="userSpaceOnUse">
        <stop stopColor="#8eb6ff" /><stop offset="1" stopColor="#4c81e3" />
      </linearGradient>
      <linearGradient id="parcel-side" x1="235" y1="180" x2="339" y2="275" gradientUnits="userSpaceOnUse">
        <stop stopColor="#5079d0" /><stop offset="1" stopColor="#294d9f" />
      </linearGradient>
    </defs>
    <circle cx="246" cy="170" r="138" fill="#3166c8" fillOpacity=".18" />
    <circle cx="246" cy="170" r="115" stroke="#a7c6fc" strokeOpacity=".28" />
    <circle cx="246" cy="170" r="154" stroke="#a7c6fc" strokeOpacity=".24" strokeDasharray="3 10" />
    <path d="M21 246c52 0 60-80 127-80s62 139 142 139c41 0 65-37 82-64" stroke="#bdd5ff" strokeOpacity=".77" strokeWidth="2" strokeLinecap="round" strokeDasharray="2 9" />
    <circle cx="28" cy="246" r="7" fill="#a7c7ff" />
    <path d="m91 266 142 71 144-75-144-74-142 78Z" fill="#081f4d" fillOpacity=".65" />
    <path d="m91 251 142 70 144-74-144-74-142 78Z" fill="#2959aa" stroke="#76a8fa" strokeOpacity=".55" />
    <path d="m124 150 108-59 109 59-109 61-108-61Z" fill="url(#parcel-lid)" />
    <path d="m124 150 108 61v96l-108-60v-97Z" fill="url(#parcel-front)" />
    <path d="m232 211 109-61v96l-109 61v-96Z" fill="url(#parcel-side)" />
    <path d="m165 128 26-14 110 59v36l-26 14v-35l-110-60Z" fill="#eef4ff" fillOpacity=".87" />
    <path d="m153 202 44 24v35l-44-25v-34Z" fill="#eff6ff" />
    <path d="m161 216 27 15m-27-7 19 11" stroke="#426cbb" strokeWidth="2" strokeLinecap="round" />
    <path d="m246 285 40-22" stroke="#96b8f7" strokeWidth="2" strokeLinecap="round" />
    <path d="M340 53c0-14 11-25 25-25s25 11 25 25c0 18-25 43-25 43s-25-25-25-43Z" fill="#eff5ff" />
    <circle cx="365" cy="52" r="9" fill="#2f66ce" />
    <path d="M62 115v18m-9-9h18m250-87v14m-7-7h14" stroke="#d9e8ff" strokeWidth="2" strokeLinecap="round" />
  </svg>;
}

function PublicHeader({ focused }: { focused: boolean }) {
  return <header className="public-topbar">
    <div className="public-layout public-topbar-inner">
      <a className="public-brand-link" href="/" aria-label="BUZON Xpress, inicio"><Brand /></a>
      {!focused && <>
        <nav aria-label="Navegación pública" className="public-nav">
          <a href="#como-funciona">Cómo funciona</a>
          <a href="#puntos">Puntos y tarifas</a>
          <a href="#seguimiento">Seguimiento</a>
        </nav>
        <a className="public-nav-action" href="#acceso">Mi cuenta</a>
      </>}
    </div>
  </header>;
}

function PublicIntro() {
  return <div className="public-hero">
    <div className="public-hero-copy">
      <p className="public-eyebrow">Custodia temporal asistida</p>
      <h1>Intercambia objetos en horarios distintos</h1>
      <p className="public-hero-detail">
        Deja el objeto en un punto atendido. Tu destinatario podrá recogerlo después, dentro del horario del punto,
        con un código temporal.
      </p>
      <a className="public-hero-link" href="#como-funciona">
        Ver cómo funciona <span aria-hidden="true">↓</span>
      </a>
    </div>
    <ServiceArt />
  </div>;
}

function PublicSteps() {
  return <section className="public-steps" id="como-funciona" aria-labelledby="steps-heading">
    <div className="public-section-intro">
      <p className="public-eyebrow">El recorrido</p>
      <h2 id="steps-heading">De la entrega al retiro</h2>
    </div>
    <ol className="public-step-list">
      <li>
        <span className="public-step-number" aria-hidden="true">01</span>
        <h3>Registra el objeto</h3>
        <p>Elige el punto, indica el contacto del destinatario y declara el tamaño. Podrás cancelar antes de depositarlo.</p>
      </li>
      <li>
        <span className="public-step-number" aria-hidden="true">02</span>
        <h3>Déjalo en el punto</h3>
        <p>El operador comprueba la capacidad, confirma el costo y registra el cobro y la ubicación al recibir el objeto.</p>
      </li>
      <li>
        <span className="public-step-number" aria-hidden="true">03</span>
        <h3>Retira con un código</h3>
        <p>El destinatario genera su código temporal. El operador lo verifica y deja constancia de la entrega realizada.</p>
      </li>
    </ol>
    <div className="public-service-note">
      <strong>Antes de ir al punto</strong>
      <p>Consulta el horario y cotiza según el tamaño y el plazo. El espacio se confirma cuando el operador recibe el objeto.</p>
      <a href="#puntos">Consultar puntos <span aria-hidden="true">→</span></a>
    </div>
  </section>;
}

export function Access({ verificationToken, resetToken, initialReference, initialCustody }: Links) {
  const [user, setUser] = useState<User | null>(null);
  const [mode, setMode] = useState<Mode>("login");
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
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 401)) throw error;
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
  }, [loading, mode, reset, token, user]);

  function changeMode(next: Mode) {
    shouldMoveFocus.current = true;
    setMode(next);
    setMessage("");
    task.setError("");
  }

  function doTask(action: () => Promise<void>) {
    setMessage("");
    void task.run(action);
  }

  const status = <Status busy={task.busy || loading} error={task.error} message={message} />;

  if (reset) {
    return <div className="public-site">
      <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
      <PublicHeader focused />
      <main className="public-layout public-task-page" id="contenido-principal" tabIndex={-1}>
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
              shouldMoveFocus.current = true;
              setReset(null);
              setUser(null);
              setMode("login");
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
      </main>
    </div>;
  }

  if (token) {
    return <div className="public-site">
      <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
      <PublicHeader focused />
      <main className="public-layout public-task-page" id="contenido-principal" tabIndex={-1}>
        <section className="public-auth-card public-verify-card" aria-labelledby="verify-heading">
          <p className="public-eyebrow">Comprobación de contacto</p>
          <h1 id="verify-heading" tabIndex={-1} ref={heading}>Comprobar correo</h1>
          <p>Confirma que tienes acceso al correo asociado a tu cuenta.</p>
          {status}
          {!loading && <button type="button" disabled={task.busy} onClick={() => doTask(async () => {
            await auth.verifyContact(token);
            shouldMoveFocus.current = true;
            setToken(null);
            setMessage("Correo comprobado.");
            if (user) setUser(await auth.me());
          })}>Confirmar correo</button>}
          <a className="public-return-link" href="/">Volver al inicio</a>
        </section>
      </main>
    </div>;
  }

  if (user && !loading) {
    return <div className="workspace-shell">
      <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
      <header className="workspace-topbar">
        <div className="workspace-topbar-inner">
          <Brand />
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
              shouldMoveFocus.current = true;
              setUser(null);
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
        {initialReference && <PublicService initialReference={initialReference} trackingOnly />}
        <Dashboard key={user.id} user={user} initialCustody={initialCustody} />
      </main>
    </div>;
  }

  const access = accessCopy[mode];
  return <div className="public-site">
    <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
    <PublicHeader focused={false} />
    <main className="public-layout public-main" id="contenido-principal" tabIndex={-1}>
      <div className="public-intro">
        <PublicIntro />
        <div className="public-access-area" id="acceso" tabIndex={-1}>
          <section className="public-auth-card" aria-labelledby="access-heading">
            <p className="public-eyebrow">Mi cuenta</p>
            <h2 id="access-heading" tabIndex={-1} ref={heading}>{access.title}</h2>
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
                    shouldMoveFocus.current = true;
                    setUser(session.user);
                    setMessage("Sesión iniciada.");
                  } else if (mode === "register") {
                    const phone = value(data, "phone");
                    await auth.register({
                      email, password, full_name: value(data, "name"), ...(phone ? { phone } : {}),
                    });
                    shouldMoveFocus.current = true;
                    setMode("login");
                    setMessage("Cuenta registrada. Comprueba tu contacto por correo o con el personal del punto.");
                  } else {
                    await auth.requestReset(email);
                    shouldMoveFocus.current = true;
                    setMode("login");
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
                  <button type="button" className="secondary" disabled={task.busy} onClick={() => changeMode("register")}>Crear cuenta</button>
                  <button type="button" className="secondary" disabled={task.busy} onClick={() => changeMode("request-reset")}>Recuperar contraseña</button>
                </> : <button type="button" className="secondary" disabled={task.busy} onClick={() => changeMode("login")}>Volver a iniciar sesión</button>}
              </nav>
            </>}
          </section>
        </div>
      </div>
      <PublicSteps />
      <PublicService initialReference={initialReference} />
    </main>
    <footer className="public-footer">
      <div className="public-layout public-footer-inner">
        <Brand />
        <p>Custodia temporal en puntos atendidos.</p>
        <a href="#acceso">Ir a mi cuenta <span aria-hidden="true">↑</span></a>
      </div>
    </footer>
  </div>;
}
