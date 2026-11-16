import { useEffect, useState } from "react";

import { auth, type MfaSetup, type MfaStatus } from "../../services/auth";
import { Field, formData, Status, useTask, value } from "../shared/forms";

export function MfaSecurity() {
  const [status, setStatus] = useState<MfaStatus | null>(null);
  const [mode, setMode] = useState<"setup" | "disable" | "rotate" | null>(null);
  const [setup, setSetup] = useState<MfaSetup | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const task = useTask();

  useEffect(() => {
    void task.run(async () => setStatus(await auth.mfaStatus()));
  }, []);

  function run(action: () => Promise<void>) {
    setMessage("");
    void task.run(action);
  }

  function close() {
    setSetup(null);
    setMode(null);
    task.setError("");
    setMessage("");
  }

  function showCodes(codes: string[]) {
    setBackupCodes(codes);
    setSetup(null);
    setMode(null);
    setStatus({ enabled: true, recovery_codes_remaining: codes.length });
  }

  return <section className="account-security" aria-labelledby="mfa-settings-heading">
    <div className="account-security-heading">
      <div>
        <p className="public-eyebrow">Protección de acceso</p>
        <h2 id="mfa-settings-heading">Seguridad de mi cuenta</h2>
      </div>
      {status && <span className="access-security-state" data-enabled={status.enabled}>
        <span aria-hidden="true">{status.enabled ? "✓" : "○"}</span>
        {status.enabled ? "Verificación en dos pasos activa" : "Verificación en dos pasos disponible"}
      </span>}
    </div>
    <p>Protege tu cuenta con tu contraseña y un código de una aplicación autenticadora. El código cambia periódicamente y se genera en tu dispositivo.</p>
    <Status busy={task.busy} error={task.error} message={message} />

    {!status && !task.busy && <button type="button" className="secondary" onClick={() =>
      run(async () => setStatus(await auth.mfaStatus()))}>Consultar configuración de seguridad</button>}

    {backupCodes.length > 0 ? <div className="access-recovery-codes" aria-labelledby="recovery-codes-heading">
      <h3 id="recovery-codes-heading">Guarda tus códigos de recuperación</h3>
      <p>Se muestran una sola vez. Guarda estos códigos en un lugar privado: cada uno permite entrar una vez si pierdes acceso a tu aplicación autenticadora.</p>
      <ul aria-label="Códigos de recuperación">{backupCodes.map((code) => <li key={code}><code>{code}</code></li>)}</ul>
      <div className="access-inline-actions">
        <button type="button" className="secondary" disabled={task.busy} onClick={() => run(async () => {
          if (!navigator.clipboard) {
            setMessage("Selecciona los códigos y cópialos para guardarlos.");
            return;
          }
          try {
            await navigator.clipboard.writeText(backupCodes.join("\n"));
            setMessage("Códigos copiados. Guárdalos antes de cerrar esta sección.");
          } catch {
            setMessage("Selecciona los códigos y cópialos manualmente para guardarlos.");
          }
        })}>Copiar códigos</button>
        <button type="button" disabled={task.busy} onClick={() => {
          setBackupCodes([]);
          setMessage("Códigos ocultos. Conserva tu copia en un lugar privado.");
        }}>Ya guardé mis códigos</button>
      </div>
    </div> : setup ? <div className="access-mfa-enrollment">
      <ol className="access-enrollment-steps">
        <li>
          <h3>Añade tu cuenta a una app autenticadora</h3>
          <p>Elige «Añadir clave de configuración» en tu aplicación y usa esta clave con códigos basados en tiempo.</p>
          <code className="access-setup-secret">{setup.secret}</code>
          <a className="access-authenticator-link" href={setup.otpauth_uri}>Abrir en mi aplicación autenticadora ↗</a>
          <small>La clave debe permanecer privada. La configuración vence a las {new Date(setup.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.</small>
        </li>
        <li>
          <h3>Confirma el primer código</h3>
          <p>La protección se activa cuando compruebes un código de seis dígitos generado por tu aplicación.</p>
          <form onSubmit={(event) => {
            const data = formData(event);
            run(async () => {
              const result = await auth.confirmMfa(value(data, "code"));
              showCodes(result.recovery_codes);
              setMessage("Verificación en dos pasos activada. Tus otras sesiones se cerraron.");
            });
          }} aria-busy={task.busy}>
            <Field label="Código de la aplicación">
              <input name="code" inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6} />
            </Field>
            <div className="access-inline-actions">
              <button type="submit" disabled={task.busy}>{task.busy && <span className="access-spinner" aria-hidden="true" />}Activar verificación</button>
              <button type="button" className="secondary" disabled={task.busy} onClick={close}>Cancelar configuración</button>
            </div>
          </form>
        </li>
      </ol>
    </div> : mode ? <form className="access-security-form" aria-busy={task.busy} onSubmit={(event) => {
      const form = event.currentTarget;
      const data = formData(event);
      run(async () => {
        const password = String(data.get("password") ?? "");
        if (mode === "setup") {
          setSetup(await auth.setupMfa(password));
          form.reset();
        } else if (mode === "disable") {
          await auth.disableMfa(password, value(data, "code"));
          setStatus({ enabled: false, recovery_codes_remaining: 0 });
          setMode(null);
          form.reset();
          setMessage("Verificación en dos pasos desactivada. Tus otras sesiones se cerraron.");
        } else {
          const result = await auth.replaceRecoveryCodes(password, value(data, "code"));
          showCodes(result.recovery_codes);
          form.reset();
          setMessage("Se generaron nuevos códigos. Los anteriores dejaron de servir y tus otras sesiones se cerraron.");
        }
      });
    }}>
      <div>
        <h3>{mode === "setup" ? "Activa la verificación en dos pasos" : mode === "disable" ? "Desactivar verificación en dos pasos" : "Renovar códigos de recuperación"}</h3>
        <p>{mode === "setup" ? "Confirma tu contraseña para preparar una clave privada de configuración." : mode === "disable"
          ? "Confirma tu contraseña y un código válido. Después ingresarás solo con tu contraseña."
          : "Los nuevos códigos reemplazarán a todos los anteriores. Confirma tu contraseña y un código de tu aplicación o uno de recuperación."}</p>
      </div>
      <Field label="Contraseña actual">
        <input name="password" type="password" autoComplete="current-password" required maxLength={128} />
      </Field>
      {mode !== "setup" && <Field label="Código de la aplicación o de recuperación">
        <input name="code" type="text" autoComplete="one-time-code" required maxLength={128} />
      </Field>}
      <div className="access-inline-actions">
        <button type="submit" disabled={task.busy}>{task.busy && <span className="access-spinner" aria-hidden="true" />}
          {mode === "setup" ? "Preparar configuración" : mode === "disable" ? "Confirmar desactivación" : "Generar nuevos códigos"}</button>
        <button type="button" className="secondary" disabled={task.busy} onClick={close}>Cancelar</button>
      </div>
    </form> : status && <div className="access-security-actions">
      <div>
        <strong>{status.enabled ? "Tu segundo factor está configurado" : "Un paso más para cuidar tu cuenta"}</strong>
        <p>{status.enabled ? "Códigos de recuperación disponibles: " + status.recovery_codes_remaining + "."
          : "Para activarla necesitas tu contraseña, un contacto comprobado y una aplicación autenticadora que genere códigos temporales."}</p>
      </div>
      <div className="access-inline-actions">
        {!status.enabled ? <button type="button" disabled={task.busy} onClick={() => setMode("setup")}>Activar verificación en dos pasos</button>
          : <>
            <button type="button" className="secondary" disabled={task.busy} onClick={() => setMode("rotate")}>Renovar códigos</button>
            <button type="button" className="secondary" disabled={task.busy} onClick={() => setMode("disable")}>Desactivar</button>
          </>}
      </div>
    </div>}
  </section>;
}
