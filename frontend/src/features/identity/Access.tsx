import { useEffect, useState } from "react";

import { ApiError } from "../../services/api";
import { auth, type User } from "../../services/auth";
import { PublicService } from "../custody/PublicService";
import { Dashboard } from "../dashboard/Dashboard";
import { Field, formData, Status, useTask, value } from "../shared/forms";

type Mode = "login" | "register" | "request-reset";

interface Links {
  verificationToken: string | null;
  resetToken: string | null;
  initialReference: string | null;
  initialCustody: string | null;
}

export function Access({ verificationToken, resetToken, initialReference, initialCustody }: Links) {
  const [user, setUser] = useState<User | null>(null);
  const [mode, setMode] = useState<Mode>("login");
  const [token, setToken] = useState(verificationToken);
  const [reset, setReset] = useState(resetToken);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
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

  function changeMode(next: Mode) {
    setMode(next);
    setMessage("");
    task.setError("");
  }

  function doTask(action: () => Promise<void>) {
    setMessage("");
    void task.run(action);
  }

  const heading = mode === "login" ? "Iniciar sesión"
    : mode === "register" ? "Crear cuenta general" : "Solicitar recuperación";
  return <main className="shell">
    <header className="hero">
      <p className="brand">BUZON Xpress</p>
      <h1>{user ? "Mi espacio de custodia" : "Custodia temporal en puntos atendidos"}</h1>
      <p>{user
        ? "Consulta tus operaciones y el estado informado por el punto."
        : "Registra un objeto, deposítalo con el operador y coordina el retiro con tu destinatario."}</p>
    </header>
    <Status busy={task.busy} error={task.error} message={message} />

    {!loading && token && <section aria-labelledby="verify-heading">
      <h2 id="verify-heading">Comprobar correo</h2>
      <button type="button" disabled={task.busy} onClick={() => doTask(async () => {
        await auth.verifyContact(token);
        setToken(null);
        setMessage("Correo comprobado.");
        if (user) setUser(await auth.me());
      })}>Confirmar correo</button>
    </section>}

    {!loading && reset && <section aria-labelledby="reset-heading">
      <h2 id="reset-heading">Cambiar contraseña</h2>
      <form aria-busy={task.busy} onSubmit={(event) => {
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
      </form>
    </section>}

    {!loading && !reset && (user ? <><section aria-labelledby="account-heading">
      <h2 id="account-heading">Mi cuenta</h2>
      <p>{user.full_name} · {user.contact_verified ? "Contacto comprobado" : "Contacto pendiente"}</p>
      <button type="button" className="secondary" disabled={task.busy} onClick={() => doTask(async () => {
        try {
          await auth.logout();
        } catch (error) {
          if (!(error instanceof ApiError && error.status === 401)) throw error;
        }
        setUser(null);
        setMessage("Sesión cerrada.");
      })}>Cerrar sesión</button>
    </section><Dashboard key={user.id} user={user} initialCustody={initialCustody} /></> : <>
      <section aria-labelledby="access-heading">
        <h2 id="access-heading">{heading}</h2>
        <form key={mode} onSubmit={(event) => {
          const form = event.currentTarget;
          const data = formData(event);
          const email = value(data, "email");
          const password = String(data.get("password") ?? "");
          doTask(async () => {
            if (mode === "login") {
              const session = await auth.login({ email, password });
              setUser(session.user);
              setMessage("Sesión iniciada.");
            } else if (mode === "register") {
              const phone = value(data, "phone");
              await auth.register({
                email, password, full_name: value(data, "name"), ...(phone ? { phone } : {}),
              });
              setMode("login");
              setMessage("Cuenta registrada. Comprueba tu contacto por correo o con el personal del punto.");
            } else {
              await auth.requestReset(email);
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
          <button type="submit" disabled={task.busy}>
            {mode === "login" ? "Entrar" : mode === "register" ? "Registrar cuenta" : "Enviar solicitud"}
          </button>
        </form>
        <nav aria-label="Opciones de acceso" className="actions">
          {mode === "login" ? <>
            <button type="button" className="secondary" disabled={task.busy} onClick={() => changeMode("register")}>Crear cuenta</button>
            <button type="button" className="secondary" disabled={task.busy} onClick={() => changeMode("request-reset")}>Recuperar contraseña</button>
          </> : <button type="button" className="secondary" disabled={task.busy} onClick={() => changeMode("login")}>Volver a iniciar sesión</button>}
        </nav>
      </section>
      <PublicService initialReference={initialReference} />
    </>)}
  </main>;
}
