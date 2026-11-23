import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useCallback, useRef, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View, type TextInputProps, type ScrollViewProps } from "react-native";
import Ionicons from "@expo/vector-icons/Ionicons";
import { c, s } from "./theme";
import type { CustodyState } from "../api/types";
import { stateLabels } from "../api/types";

export function Button({ title, onPress, busy = false, secondary = false, danger = false, disabled = false }: {
  title: string; onPress: () => void; busy?: boolean; secondary?: boolean; danger?: boolean; disabled?: boolean;
}) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled: disabled || busy, busy }}
    disabled={disabled || busy} onPress={onPress} style={({ pressed }) => [styles.button,
      secondary && styles.secondary, danger && { backgroundColor: c.red }, (pressed || disabled || busy) && { opacity: .65 }]}>
    {busy && <ActivityIndicator color={secondary ? c.navy : "white"} />}
    <Text style={[styles.buttonText, secondary && { color: c.navy }]}>{title}</Text>
  </Pressable>;
}
export function RequiredMark() {
  return <Text accessibilityLabel="Obligatorio" style={{ color: c.red }}> *</Text>;
}
export function Field({ label, required = false, ...props }: TextInputProps & { label: string; required?: boolean }) {
  return <View style={{ gap: 7 }}><Text style={s.label}>{label}{required && <RequiredMark />}</Text>
    <TextInput accessibilityLabel={required ? label + ", obligatorio" : label} placeholderTextColor="#718097" {...props}
      style={[styles.input, props.multiline && { minHeight: 100, textAlignVertical: "top" }, props.style]} /></View>;
}
export function Password({ label = "Contraseña", value, onChangeText, isNew = false }: {
  label?: string; value: string; onChangeText: (value: string) => void; isNew?: boolean;
}) {
  const [show, setShow] = useState(false);
  return <View style={{ gap: 7 }}><Text style={s.label}>{label}<RequiredMark /></Text><View style={styles.passwordRow}>
    <TextInput accessibilityLabel={label + ", obligatorio"} value={value} onChangeText={onChangeText} secureTextEntry={!show}
      autoCapitalize="none" autoCorrect={false} autoComplete={isNew ? "new-password" : "current-password"}
      style={[styles.input, { flex: 1, borderWidth: 0 }]} maxLength={128} />
    <Pressable accessibilityRole="button" accessibilityLabel={show ? "Ocultar " + label : "Mostrar " + label}
      onPress={() => setShow(!show)} style={{ padding: 13 }}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name={show ? "eye-off-outline" : "eye-outline"} size={21} color={c.navy} /></Pressable>
  </View></View>;
}
export function Feedback({ error, message, busy }: { error?: string; message?: string; busy?: boolean }) {
  if (!error && !message && !busy) return null;
  return <View accessibilityLiveRegion="polite" style={[styles.feedback, error ? { backgroundColor: "#fff0f2", borderColor: "#f1ccd5" } : {}]}>
    {busy && <ActivityIndicator color={c.blue} />}<Text accessibilityRole={error ? "alert" : undefined}
      style={{ color: error ? "#841c2e" : c.navy, fontSize: 14, lineHeight: 22, flexShrink: 1 }}>{error || message || "Consultando…"}</Text></View>;
}
export function Empty({ title, detail }: { title: string; detail: string }) {
  return <View style={[s.card, { alignItems: "center", paddingVertical: 30 }]}>
    <Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="cube-outline" size={35} color={c.blue} /><Text style={[s.h2, { textAlign: "center" }]}>{title}</Text><Text style={[s.muted, { textAlign: "center" }]}>{detail}</Text></View>;
}
export function Badge({ state }: { state: CustodyState }) {
  const done = ["RETIRADA", "DEVUELTA"].includes(state);
  return <View style={{ alignSelf: "flex-start", backgroundColor: done ? "#e6f5ed" : c.pale, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 20 }}>
    <Text style={{ color: done ? c.good : c.navy, fontWeight: "700", fontSize: 11 }}>{stateLabels[state]}</Text></View>;
}
export function Chips<T extends string>({ options, value, onChange, disabled = false }: { options: { value: T; label: string }[]; value: T; onChange: (value: T) => void; disabled?: boolean }) {
  return <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>{options.map(option =>
    <Pressable key={option.value} accessibilityRole="radio" accessibilityState={{ checked: option.value === value, disabled }} disabled={disabled}
      onPress={() => onChange(option.value)} style={[styles.chip, option.value === value && { backgroundColor: c.navy, borderColor: c.navy }]}>
      <Text style={{ color: option.value === value ? "white" : c.ink, fontWeight: "600", fontSize: 13, flexShrink: 1 }}>{option.label}</Text>
    </Pressable>)}</View>;
}
export function Page({ children, style, contentContainerStyle, ...props }: ScrollViewProps) {
  return <KeyboardAwareScrollView bottomOffset={48} extraKeyboardSpace={24} disableScrollOnKeyboardHide
    keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" style={[s.page, style]}
    contentContainerStyle={[s.content, contentContainerStyle]} {...props}>{children}</KeyboardAwareScrollView>;
}
export function useAction() {
  const active = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const run = useCallback(async (action: () => Promise<void>) => {
    if (active.current) return;
    active.current = true; setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : "No se pudo completar la solicitud."); }
    finally { active.current = false; setBusy(false); }
  }, []);
  return { busy, error, message, run, setError, setMessage };
}
export const styles = StyleSheet.create({
  input: { borderWidth: 1, borderColor: "#bac7db", borderRadius: 13, backgroundColor: "#fcfdff", color: c.ink, minHeight: 50, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15 },
  passwordRow: { flexDirection: "row", alignItems: "center", borderWidth: 1, borderColor: "#bac7db", borderRadius: 13, backgroundColor: "#fcfdff" },
  button: { minHeight: 50, paddingHorizontal: 19, paddingVertical: 13, backgroundColor: c.blue, borderRadius: 13, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 9 },
  secondary: { backgroundColor: "white", borderColor: c.border, borderWidth: 1 },
  buttonText: { flexShrink: 1, fontWeight: "700", color: "white", fontSize: 14, textAlign: "center" },
  feedback: { padding: 14, borderRadius: 13, backgroundColor: c.pale, borderWidth: 1, borderColor: "#d5e3f9", flexDirection: "row", alignItems: "center", gap: 9 },
  chip: { maxWidth: "100%", minHeight: 44, justifyContent: "center", borderWidth: 1, borderColor: c.border, borderRadius: 30, paddingHorizontal: 14, paddingVertical: 10, backgroundColor: "white" },
});
