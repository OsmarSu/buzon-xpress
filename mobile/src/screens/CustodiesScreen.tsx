import type { RegistrationDraft } from "../navigation/paths";
import { useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Alert, AppState, Modal, Pressable, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useSession } from "../auth/SessionProvider";
import { Badge, Button, Chips, Empty, Feedback, Field, RequiredMark, Page, useAction } from "../components/ui";
import { c, s } from "../components/theme";
import { dateLabel, sizeMeasurementNote, sizes, type Credential, type Custody, type Point, type Quote, type Registered, type Size } from "../api/types";

function Sheet({ visible, title, onClose, children }: { visible: boolean; title: string; onClose: () => void; children: ReactNode }) {
  return <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
    <SafeAreaView style={s.page}><View style={{ paddingHorizontal: 20, paddingVertical: 13, borderBottomWidth: 1, borderColor: c.border, backgroundColor: "white" }}>
      <Pressable accessibilityRole="button" accessibilityLabel="Volver a mis custodias" onPress={onClose} style={[s.row, { minHeight: 38 }]}>
        <Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="arrow-back" size={22} color={c.navy} /><Text style={[s.h2, s.flex]}>{title}</Text>
      </Pressable>
    </View>{children}</SafeAreaView>
  </Modal>;
}
const filters = [{ value: "", label: "Todas" }, { value: "REGISTRADA", label: "Pendientes" }, { value: "EN_CUSTODIA", label: "En custodia" }, { value: "RETIRADA", label: "Retiradas" }, { value: "DEVUELTA", label: "Devueltas" }, { value: "CANCELADA", label: "Canceladas" }];
export function CustodiesScreen({ openId, onCloseLink, draft, onConsumeDraft }: { openId?: string | null; onCloseLink?: () => void; draft?: RegistrationDraft; onConsumeDraft?: () => void }) {
  const { client, user } = useSession();
  const [items, setItems] = useState<Custody[] | null>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [filter, setFilter] = useState("");
  const [creating, setCreating] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Custody | null>(null);
  const [reference, setReference] = useState<string | null>(null);
  const [credential, setCredential] = useState<Credential | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [cancelReason, setCancelReason] = useState("");
  const [pointId, setPointId] = useState("");
  const [size, setSize] = useState<Size>("PEQUENO");
  const [recipient, setRecipient] = useState("");
  const [description, setDescription] = useState("");
  const [hours, setHours] = useState("24");
  const [quote, setQuote] = useState<Quote | null>(null);
  const listTask = useAction(); const detailTask = useAction(); const action = useAction(); const price = useAction();
  const create = useRef(client.mutation()).current;
  const cancel = useRef(client.mutation()).current;
  const requestId = useRef<string | null>(null);
  const credentialGeneration = useRef(0);
  const { run: runList } = listTask;
  const { run: runDetail } = detailTask;
  const { setError, setMessage } = action;
  const reload = useCallback(() => {
    void runList(async () => {
      const [records, locations] = await Promise.all([client.list(filter), client.points()]);
      setItems(records); setPoints(locations);
    });
  }, [client, filter, runList]);
  useFocusEffect(reload);
  useFocusEffect(useCallback(() => {
    if (!draft || !user?.contact_verified) return;
    setPointId(draft.pointId); setSize(draft.size); setHours(draft.hours); setQuote(null);
    setError(""); setMessage(""); setCreating(true);
    onConsumeDraft?.();
  }, [draft, user?.contact_verified, onConsumeDraft, setError, setMessage]));
  const opening = useRef(false);
  const openDetail = useCallback(async function openDetail(id: string, publicReference?: string) {
    if (opening.current) return;
    opening.current = true;
    credentialGeneration.current += 1;
    requestId.current = id; setSelectedId(id); setSelected(null);
    setCredential(null); setReference(publicReference || null); setCancelReason("");
    setError(""); setMessage("");
    try { await runDetail(async () => { const result = await client.detail(id); if (requestId.current === id) setSelected(result); }); }
    finally { opening.current = false; }
  }, [client, runDetail, setError, setMessage]);
  useFocusEffect(useCallback(() => { if (openId) void openDetail(openId); }, [openId, openDetail]));
  useEffect(() => {
    const listener = AppState.addEventListener("change", state => { if (state !== "active") { credentialGeneration.current += 1; setCredential(null); } });
    return () => listener.remove();
  }, []);
  useEffect(() => {
    if (!credential) return;
    const tick = () => { const time = Date.now(); setNow(time); if (Date.parse(credential.expires_at) <= time) setCredential(null); };
    const timer = setInterval(tick, 1000);
    const expiry = setTimeout(() => setCredential(null), Math.max(0, Date.parse(credential.expires_at) - Date.now()));
    return () => { clearInterval(timer); clearTimeout(expiry); };
  }, [credential]);
  function closeDetail() { credentialGeneration.current += 1; requestId.current = null; setSelectedId(null); setSelected(null); setCredential(null); setReference(null); onCloseLink?.(); }
  async function obtainCredential(id: string, reissue: boolean) {
    const generation = credentialGeneration.current;
    const result = await client.issue(id, reissue);
    if (requestId.current === id && credentialGeneration.current === generation && AppState.currentState === "active" && Date.parse(result.expires_at) > Date.now()) {
      setNow(Date.now()); setCredential(result);
    }
  }
  async function submitRegistration() {
    if (!points.some(point => point.id === pointId)) throw new Error("Selecciona un punto activo de la lista.");
    if (!recipient.trim()) throw new Error("Ingresa el correo o teléfono del destinatario registrado.");
    if (!description.trim()) throw new Error("Describe el objeto y su embalaje.");
    const result = await create<Registered>("/custodies", { point_id: pointId, recipient_contact: recipient.trim(), description: description.trim(), size_category: size });
    setCreating(false); setDescription(""); setRecipient(""); setQuote(null);
    await openDetail(result.id, result.public_reference); reload();
    action.setMessage("Objeto registrado. Preséntalo al personal del punto dentro de su horario.");
  }
  const selectedPoint = points.find(point => point.id === selected?.point_id);
  return <>
    <Page><View style={s.between}><View style={s.flex}><Text style={s.eyebrow}>TU ACTIVIDAD</Text><Text accessibilityRole="header" style={s.title}>Mis custodias</Text></View>
      <Pressable accessibilityRole="button" accessibilityLabel="Actualizar custodias" onPress={reload} disabled={listTask.busy} style={{ padding: 12, backgroundColor: c.pale, borderRadius: 14 }}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="refresh-outline" size={23} color={c.blue} /></Pressable>
    </View><Text style={s.muted}>Consulta los objetos que registraste y los que recibirás.</Text>
    {user?.contact_verified ? <Button title="Registrar un objeto" onPress={() => { action.setError(""); action.setMessage(""); setCreating(true); }} />
      : <Feedback message="Verifica tu correo para habilitar el registro de objetos. Puedes consultar tus custodias existentes." />}
    <Chips options={filters} value={filter} onChange={setFilter} /><Feedback {...listTask} />
    {listTask.error && <Button title="Volver a consultar" secondary onPress={reload} />}
    {items?.length === 0 && <Empty title="No hay registros para mostrar" detail={filter ? "Prueba con otro estado para consultar tus custodias." : "Registra un objeto o espera a que otra persona registre uno para ti."} />}
    {items?.map(item => <Pressable key={item.id} accessibilityRole="button" disabled={detailTask.busy}
      onPress={() => void openDetail(item.id)} style={s.card}>
      <View style={s.between}><View style={{ backgroundColor: c.pale, padding: 10, borderRadius: 13 }}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="cube-outline" size={25} color={c.blue} /></View><Badge state={item.state} /></View>
      <Text style={s.label}>{item.description}</Text><Text style={s.small}>{points.find(point => point.id === item.point_id)?.name || "Punto de servicio"}</Text>
      <Text style={s.small}>Guía privada: {item.tracking_number}</Text>
      <View style={s.between}><Text style={s.small}>{item.due_at ? "Plazo: " + dateLabel(item.due_at) : "Pendiente de recepción"}</Text><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="arrow-forward" size={19} color={c.blue} /></View>
    </Pressable>)}
    </Page>
    <Sheet visible={creating} title="Registrar un objeto" onClose={() => { if (!action.busy) setCreating(false); }}>
      <Page><Feedback {...listTask} /><Text style={s.muted}>El registro no reserva espacio. El personal confirma capacidad, ubicación e importe al recibir el objeto.</Text>
        <View style={s.card}><Text accessibilityRole="header" style={s.h2}>1. Elige el punto<RequiredMark /></Text>
          {points.map(point => <Pressable key={point.id} accessibilityRole="radio" accessibilityState={{ checked: pointId === point.id }}
            onPress={() => { setPointId(point.id); setQuote(null); }} style={{ padding: 14, borderWidth: 1, borderColor: pointId === point.id ? c.blue : c.border, borderRadius: 13, backgroundColor: pointId === point.id ? c.pale : "white", gap: 5 }}>
            <Text style={s.label}>{point.name}</Text><Text style={s.small}>{point.address}</Text>
          </Pressable>)}
          {!listTask.busy && !points.length && <Text style={s.muted}>No hay puntos disponibles. Vuelve a consultar antes de registrar.</Text>}
        </View>
        <View style={s.card}><Text accessibilityRole="header" style={s.h2}>2. Datos del objeto</Text>
          <Field required label="Correo o teléfono del destinatario" placeholder="Contacto exacto de su cuenta" value={recipient} onChangeText={setRecipient} autoCapitalize="none" autoCorrect={false} maxLength={254} />
          <Text style={s.small}>El destinatario debe estar registrado y tener su contacto comprobado.</Text>
          <Text style={s.label}>Tamaño declarado<RequiredMark /></Text><Chips options={sizes} value={size} onChange={v => { setSize(v); setQuote(null); }} />
          <Text style={s.small}>{sizeMeasurementNote}</Text>
          <Field required label="Descripción externa" placeholder="Tipo de objeto, embalaje y condición visible" value={description} onChangeText={setDescription} multiline maxLength={255} />
        </View>
        <View style={s.card}><Text accessibilityRole="header" style={s.h2}>3. Consulta el importe</Text>
          <Field label="Horas para cotizar" keyboardType="number-pad" value={hours} onChangeText={v => { setHours(v); setQuote(null); }} maxLength={6} />
          <Button title="Consultar tarifa" secondary busy={price.busy} disabled={!pointId} onPress={() => void price.run(async () => {
            if (!Number.isSafeInteger(Number(hours)) || Number(hours) < 1) throw new Error("Escribe una cantidad entera de horas mayor que cero.");
            setQuote(await client.quote(pointId, size, Number(hours)));
          })} /><Feedback {...price} />
          {quote && <Text style={[s.h2, { color: c.navy }]}>Bs {quote.amount} · {quote.duration_hours} horas</Text>}
          <Text style={s.small}>Esta cotización es orientativa. El plazo y el importe se confirman en la recepción.</Text>
        </View>
        <Feedback {...action} /><Button title="Registrar objeto" busy={action.busy} disabled={!points.length} onPress={() => void action.run(submitRegistration)} />
      </Page>
    </Sheet>
    <Sheet visible={!!selectedId} title="Detalle de custodia" onClose={closeDetail}>
      <Page><Feedback {...detailTask} />
        {detailTask.error && selectedId && <Button title="Volver a consultar el detalle" secondary onPress={() => void openDetail(selectedId)} />}
        {selected && <>
          <View style={s.card}><Badge state={selected.state} /><Text accessibilityRole="header" style={s.h2}>{selected.description}</Text>
            <Text selectable style={s.small}>Guía privada: {selected.tracking_number}</Text>
            <View style={{ height: 1, backgroundColor: c.border }} />
            <Text style={s.label}>{selectedPoint?.name || "Punto de servicio"}</Text>
            {!!selectedPoint && <Text style={s.muted}>{selectedPoint.address}</Text>}
            <Text style={s.muted}>Tamaño: {sizes.find(size => size.value === selected.size_category)?.label}</Text>
            <Text style={s.muted}>Importe: {selected.state === "REGISTRADA" ? "Por confirmar en recepción" : "Bs " + selected.service_total}</Text>
            {selected.due_at && <Text style={s.muted}>Plazo: {dateLabel(selected.due_at)} · La Paz</Text>}
          </View>
          <Feedback {...action} />
          {selected.state === "EN_CUSTODIA" && <View style={s.card}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="key-outline" size={28} color={c.blue} />
            <Text accessibilityRole="header" style={s.h2}>Código de retiro</Text><Text style={s.muted}>Si eres el destinatario, obtén tu código al recoger el objeto y muéstralo solo al operador.</Text>
            {credential && <View style={{ backgroundColor: c.pale, padding: 22, borderRadius: 17, gap: 9 }}>
              <Text selectable style={{ color: c.navy, fontSize: 36, letterSpacing: 8, fontWeight: "800", textAlign: "center" }}>{credential.code}</Text>
              <Text style={[s.small, { textAlign: "center" }]}>Vence en {Math.max(0, Math.ceil((Date.parse(credential.expires_at) - now)/1000))} segundos.</Text>
              <Text style={s.small}>Se oculta al salir de este detalle o al cambiar de aplicación.</Text>
            </View>}
            <Button title={credential ? "Reemitir código de retiro" : "Obtener código de retiro"} busy={action.busy} onPress={() => {
              if (credential) Alert.alert("Reemitir código", "El código anterior dejará de servir.", [
                { text: "Cancelar", style: "cancel" }, { text: "Reemitir", onPress: () => void action.run(async () => obtainCredential(selected.id, true)) },
              ]);
              else void action.run(async () => obtainCredential(selected.id, false));
            }} />
            {!credential && <Button title="Reemplazar un código anterior" secondary busy={action.busy} onPress={() => Alert.alert(
              "Reemplazar código", "El código anterior dejará de servir. Obtén uno nuevo al recoger el objeto.",
              [{ text: "Cancelar", style: "cancel" }, { text: "Reemplazar", onPress: () => void action.run(async () => obtainCredential(selected.id, true)) }],
            )} />}
          </View>}
          <View style={s.card}><Text accessibilityRole="header" style={s.h2}>Código de Paquete</Text><Text style={s.muted}>El código de paquete permite consultar el estado, el punto y su horario.</Text>
            {reference && <Text selectable style={[s.small, { color: c.navy, backgroundColor: c.pale, padding: 15, borderRadius: 12 }]}>{reference}</Text>}
            <Button title="Renovar código de paquete" secondary busy={action.busy} onPress={() => Alert.alert("Renovar código de paquete", "El código anterior dejará de funcionar.", [
              { text: "Cancelar", style: "cancel" }, { text: "Renovar", onPress: () => void action.run(async () => { const result = await client.rotate(selected.id); setReference(result.public_reference); }) },
            ])} />
          </View>
          {selected.state === "REGISTRADA" && <View style={s.card}><Text accessibilityRole="header" style={s.h2}>Cancelar el registro</Text>
            <Text style={s.muted}>Si registraste este objeto, puedes cancelar antes de que el punto lo reciba.</Text>
            <Field required label="Motivo de cancelación" placeholder="Explica por qué ya no se necesita la custodia" value={cancelReason} onChangeText={setCancelReason} maxLength={255} multiline />
            <Button title="Solicitar cancelación" secondary busy={action.busy} onPress={() => {
              if (cancelReason.trim().length < 3) { action.setError("Escribe un motivo de al menos tres caracteres."); return; }
              Alert.alert("Cancelar registro", "Esta acción cancela la custodia pendiente de recepción.", [
                { text: "Volver", style: "cancel" }, { text: "Confirmar cancelación", style: "destructive", onPress: () => void action.run(async () => {
                  setSelected(await cancel<Custody>("/custodies/" + selected.id + "/cancel", { expected_version: selected.version, reason: cancelReason.trim() }));
                  setCredential(null); reload(); action.setMessage("Registro cancelado.");
                }) },
              ]);
            }} />
          </View>}
        </>}
      </Page>
    </Sheet>
  </>;
}
