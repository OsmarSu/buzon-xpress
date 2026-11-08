import { useEffect, useState, type FormEvent } from "react";

import { ApiError, auth, type User } from "../../services/auth";

function describeError(error: unknown): string {
  if (!(error instanceof ApiError)) return "Ocurrió un problema al procesar la respuesta.";
  if (!error.correlationId) return error.message;
  return error.message + " Referencia: " + error.correlationId;
}

export function Access({ verificationToken }: { verificationToken: string | null }) {
  const [user, setUser] = useState<User | null>(null);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [token, setToken] = useState(verificationToken);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void auth.me()
      .then(setUser)
      .catch((cause: unknown) => {
        if (!(cause instanceof ApiError && cause.status === 401)) setError(describeError(cause));
      })
      .finally(() => setLoading(false));
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const email = String(fields.get("email")).trim();
    const password = String(fields.get("password"));
    void run(async () => {
      if (mode === "login") {
        const session = await auth.login({ email, password });
        setUser(session.user);
        setMessage("Sesión iniciada.");
      } else {
        const full_name = String(fields.get("name")).trim();
        const phone = String(fields.get("phone")).trim();
        await auth.register({ email, password, full_name, ...(phone ? { phone } : {}) });
        setMode("login");
        setMessage("Cuenta registrada. Usa el enlace enviado a tu correo si el servicio de correo está habilitado.");
      }
      form.reset();
    });
  }

  function logout() {
    void run(async () => {
      try {
        await auth.logout();
      } catch (cause) {
        if (!(cause instanceof ApiError && cause.status === 401)) throw cause;
      }
      setUser(null);
      setMessage("Sesión cerrada.");
    });
  }

  function verify() {
    const link = token;
    if (!link) return;
    void run(async () => {
      await auth.verifyContact(link);
      setToken(null);
      setMessage("Correo comprobado. Inicia sesión para continuar.");
      try {
        setUser(await auth.me());
        setMessage("Correo comprobado.");
      } catch (cause) {
        if (!(cause instanceof ApiError && cause.status === 401)) throw cause;
        setUser(null);
      }
    });
  }

  return (
    <main className="access">
      <header>
        <p className="brand">BUZON Xpress</p>
        <h1>Acceso al servicio</h1>
        <p>Custodia temporal de objetos en puntos atendidos.</p>
      </header>

      <p role="status">{loading ? "Comprobando sesión…" : message}</p>
      {error && <p className="error" role="alert">{error}</p>}

      {!loading && token && (
        <section aria-labelledby="verify-heading">
          <h2 id="verify-heading">Comprobar correo</h2>
          <button type="button" disabled={busy} onClick={verify}>Confirmar correo</button>
        </section>
      )}

      {!loading && (user ? (
        <section aria-labelledby="account-heading">
          <h2 id="account-heading">Mi cuenta</h2>
          <p>{user.full_name}</p>
          <p>{user.contact_verified ? "Contacto comprobado" : "Contacto pendiente de comprobación"}</p>
          <button type="button" disabled={busy} onClick={logout}>Cerrar sesión</button>
        </section>
      ) : (
        <section aria-labelledby="access-heading">
          <h2 id="access-heading">{mode === "login" ? "Iniciar sesión" : "Crear cuenta general"}</h2>
          <form key={mode} onSubmit={submit} aria-busy={busy}>
            {mode === "register" && (
              <>
                <label htmlFor="name">Nombre completo</label>
                <input id="name" name="name" autoComplete="name" required maxLength={160} />
                <label htmlFor="phone">Teléfono (opcional)</label>
                <input id="phone" name="phone" type="tel" autoComplete="tel" maxLength={24} />
              </>
            )}
            <label htmlFor="email">Correo electrónico</label>
            <input id="email" name="email" type="email" autoComplete="username" required maxLength={254} />
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              aria-describedby={mode === "register" ? "password-hint" : undefined}
              required
              minLength={mode === "register" ? 15 : 1}
              maxLength={128}
            />
            {mode === "register" && <small id="password-hint">Usa al menos 15 caracteres.</small>}
            <button type="submit" disabled={busy}>
              {mode === "login" ? "Entrar" : "Registrar cuenta"}
            </button>
          </form>
          <button
            className="secondary"
            type="button"
            disabled={busy}
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError("");
              setMessage("");
            }}
          >
            {mode === "login" ? "Crear una cuenta" : "Volver a iniciar sesión"}
          </button>
        </section>
      ))}
    </main>
  );
}
