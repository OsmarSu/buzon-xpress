import { useState } from "react";
import { Pressable, Text, View } from "react-native";
import Ionicons from "@expo/vector-icons/Ionicons";
import { Button, Feedback, Field, Page, Password, useAction } from "../components/ui";
import { c, s } from "../components/theme";
import { useSession } from "./SessionProvider";
import type { MfaChallenge } from "../api/types";

export type AuthMode = "login" | "register" | "reset";
export function AuthScreen({ initialMode, onClose, onSuccess }: { initialMode: AuthMode; onClose: () => void; onSuccess: () => void }) {
  const { client, signIn, verify } = useSession();
  const [mode, setMode] = useState(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [challenge, setChallenge] = useState<MfaChallenge | null>(null);
  const [code, setCode] = useState("");
  const [recovery, setRecovery] = useState(false);
  const task = useAction();
  function change(next: AuthMode) {
    setMode(next); setPassword(""); setConfirmation(""); setChallenge(null); setCode("");
    task.setError(""); task.setMessage("");
  }
  const title = challenge ? "Verifica que eres tú" : mode === "register" ? "Crea tu cuenta" : mode === "reset" ? "Recupera tu acceso" : "Bienvenido de nuevo";
  async function submit() {
    if (challenge) {
      if (Date.parse(challenge.expires_at) <= Date.now()) throw new Error("La solicitud venció. Vuelve a iniciar sesión.");
      if (!code.trim()) throw new Error("Ingresa el código de tu aplicación o uno de recuperación.");
      if (!recovery && !/^[0-9]{6}$/.test(code.trim())) throw new Error("Ingresa el código de seis dígitos de tu aplicación.");
      await verify(challenge.challenge_token, code); setCode(""); onSuccess(); return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) throw new Error("Escribe un correo electrónico válido.");
    if (mode === "reset") {
      await client.requestReset(email.trim().toLowerCase());
      change("login"); task.setMessage("Si hay una cuenta habilitada con ese correo, recibirás un enlace para cambiar la contraseña."); return;
    }
    if (!password) throw new Error("Ingresa tu contraseña de BUZON Xpress.");
    if (mode === "register") {
      if (!name.trim()) throw new Error("Escribe tu nombre y apellido.");
      if (password.length < 15) throw new Error("Usa una contraseña de al menos 15 caracteres.");
      if (password !== confirmation) throw new Error("Las contraseñas deben coincidir.");
      await client.register({ email: email.trim().toLowerCase(), password, full_name: name.trim(), ...(phone.trim() ? { phone: phone.trim() } : {}) });
      change("login"); task.setMessage("Cuenta creada. Abre el enlace que recibirás por correo y verifica tu contacto. Luego vuelve para iniciar sesión."); return;
    }
    const next = await signIn(email, password);
    setPassword("");
    if (next) { setChallenge(next); return; }
    onSuccess();
  }
  return <View style={s.page}>
    <Page><Pressable accessibilityRole="button" accessibilityLabel="Volver" onPress={onClose} disabled={task.busy} style={[s.row, { minHeight: 44 }]}>
      <Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="arrow-back" size={22} color={c.navy} /><Text style={{ color: c.navy, fontWeight: "600" }}>Volver</Text>
    </Pressable>
    <View style={{ paddingVertical: 8, gap: 10 }}>
      <Text style={s.eyebrow}>TU CUENTA DE BUZON XPRESS</Text><Text accessibilityRole="header" style={[s.title, { fontSize: 34, lineHeight: 39 }]}>{title}</Text>
      <Text style={s.muted}>{challenge ? "Completa la comprobación para entrar a tu cuenta." : mode === "register" ? "Registra tus datos para consultar y gestionar tus custodias." : mode === "reset" ? "Usa el correo con el que registraste tu cuenta." : "Ingresa el correo y la contraseña que registraste en BUZON Xpress."}</Text>
    </View>
    <View style={s.card}>
      <Feedback {...task} />
      {challenge ? <>
        <Field label={recovery ? "Código de recuperación" : "Código de la aplicación"} value={code} onChangeText={setCode}
          keyboardType={recovery ? "default" : "number-pad"} maxLength={recovery ? 64 : 6} autoCapitalize="none" autoCorrect={false} autoComplete="one-time-code" />
        <Text style={s.small}>{recovery ? "Cada código de recuperación se utiliza una sola vez." : "Abre tu aplicación autenticadora y usa el código vigente de seis dígitos."}</Text>
        <Button title="Verificar y entrar" busy={task.busy} onPress={() => void task.run(submit)} />
        <Button title={recovery ? "Usar mi aplicación autenticadora" : "Usar un código de recuperación"} secondary disabled={task.busy} onPress={() => { setRecovery(!recovery); setCode(""); task.setError(""); }} />
        <Button title="Volver a iniciar sesión" secondary disabled={task.busy} onPress={() => change("login")} />
      </> : <>
        {mode === "register" && <>
          <Field label="Nombre completo" placeholder="Tu nombre y apellido" value={name} onChangeText={setName} autoComplete="name" maxLength={160} />
          <Field label="Teléfono (opcional)" placeholder="Número de contacto" value={phone} onChangeText={setPhone} keyboardType="phone-pad" autoComplete="tel" maxLength={24} />
        </>}
        <Field label="Correo electrónico" placeholder="nombre@correo.com" value={email} onChangeText={setEmail}
          autoCapitalize="none" autoCorrect={false} keyboardType="email-address" autoComplete="email" maxLength={254} />
        {mode !== "reset" && <Password value={password} onChangeText={setPassword} isNew={mode === "register"} />}
        {mode === "register" && <>
          <Text style={s.small}>Usa una frase de al menos 15 caracteres que solo tú conozcas.</Text>
          <Password label="Repetir contraseña" value={confirmation} onChangeText={setConfirmation} isNew />
        </>}
        <Button title={mode === "register" ? "Crear mi cuenta" : mode === "reset" ? "Enviar instrucciones" : "Entrar a mi cuenta"} busy={task.busy} onPress={() => void task.run(submit)} />
      </>}
    </View>
    {!challenge && <View style={{ gap: 8 }}>
      <Button title={mode === "login" ? "Crear una cuenta" : "Ya tengo cuenta"} secondary disabled={task.busy} onPress={() => change(mode === "login" ? "register" : "login")} />
      {mode === "login" && <Button title="Olvidé mi contraseña" secondary disabled={task.busy} onPress={() => change("reset")} />}
    </View>}
    <Text style={[s.small, { textAlign: "center" }]}>Tu información y las acciones de tu cuenta se consultan de forma privada.</Text>
    </Page>
  </View>;
}
