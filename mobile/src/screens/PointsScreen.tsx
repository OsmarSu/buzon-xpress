import { router, useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Keyboard, Pressable, Text, View } from "react-native";
import { useSession } from "../auth/SessionProvider";
import { Button, Chips, Empty, Feedback, Field, RequiredMark, Page, useAction } from "../components/ui";
import { NavigationIcon } from "../components/NavigationIcon";
import { OpeningHours } from "../components/OpeningHours";
import { c, s } from "../components/theme";
import { sizeMeasurementNote, sizes, type Point, type Quote, type Size } from "../api/types";

export function PointsScreen() {
  const { client, user } = useSession();
  const [points, setPoints] = useState<Point[] | null>(null);
  const [query, setQuery] = useState("");
  const [pointId, setPointId] = useState("");
  const [size, setSize] = useState<Size>("PEQUENO");
  const [hours, setHours] = useState("24");
  const [quote, setQuote] = useState<Quote | null>(null);
  const load = useAction(); const price = useAction();
  const { run } = load;
  const reload = useCallback(() => { void run(async () => setPoints(await client.points())); }, [client, run]);
  useFocusEffect(reload);
  const point = points?.find(item => item.id === pointId);
  const matches = points?.filter(item => (item.name + " " + item.address).toLocaleLowerCase("es").includes(query.trim().toLocaleLowerCase("es")));
  function validHours() {
    if (!/^[0-9]{1,6}$/.test(hours) || Number(hours) < 1) throw new Error("Indica una cantidad entera de horas, mayor que cero.");
    return Number(hours);
  }
  if (point) return <Page key={point.id}>
    <Button title="Ver otros puntos" secondary disabled={price.busy} onPress={() => { Keyboard.dismiss(); setPointId(""); setQuote(null); price.setError(""); }} />
    <Text style={s.eyebrow}>PUNTO SELECCIONADO</Text>
    <Text accessibilityRole="header" style={s.title}>{point.name}</Text>
    <View style={s.card}>
      <View style={s.row}><NavigationIcon name="points" /><Text style={[s.label, s.flex]}>Dirección de atención</Text></View>
      <Text selectable style={s.text}>{point.address}</Text>
      <Text accessibilityRole="header" style={s.h2}>Horario de atención</Text>
      <OpeningHours hours={point.opening_hours} />
    </View>
    <View style={s.card}>
      <Text accessibilityRole="header" style={s.h2}>Calcula el importe</Text>
      <Text style={s.label}>Tamaño del objeto<RequiredMark /></Text>
      <Chips options={sizes} value={size} disabled={price.busy} onChange={value => { setSize(value); setQuote(null); price.setError(""); }} />
      <Text style={s.small}>{sizeMeasurementNote}</Text>
      <Field required label="Plazo en horas" editable={!price.busy} value={hours} onChangeText={value => { setHours(value); setQuote(null); price.setError(""); }}
        keyboardType="number-pad" maxLength={6} returnKeyType="done" />
      <Button title="Calcular importe" secondary busy={price.busy} onPress={() => void price.run(async () => {
        setQuote(null); setQuote(await client.quote(point.id, size, validHours()));
      })} /><Feedback {...price} />
      {quote && <View style={{ backgroundColor: c.pale, padding: 18, borderRadius: 14, gap: 5 }}>
        <Text style={{ color: c.navy, fontSize: 30, fontWeight: "800" }}>Bs {quote.amount}</Text>
        <Text style={s.small}>Importe orientativo para {quote.duration_hours} horas.</Text>
      </View>}
      <Text style={s.small}>El personal confirma capacidad e importe al recibir el objeto. El prerregistro no reserva espacio.</Text>
    </View>
    <View style={s.card}>
      <Text accessibilityRole="header" style={s.h2}>Prepara tu registro</Text>
      <Text style={s.muted}>Continúa con este punto, el tamaño y el plazo seleccionados. Completarás el destinatario y la descripción en el siguiente paso.</Text>
      {!user?.contact_verified && <Feedback message="Verifica tu correo antes de registrar un objeto." />}
      <Button title="Registrar objeto en este punto" disabled={!user?.contact_verified || price.busy} onPress={() => void price.run(async () => {
        validHours();
        Keyboard.dismiss();
        router.navigate({ pathname: "/custodias", params: { crear: "1", point: point.id, size, hours: String(Number(hours)) } });
      })} />
    </View>
  </Page>;
  return <Page key="points-list">
    <Text style={s.eyebrow}>PLANIFICA TU VISITA</Text><Text accessibilityRole="header" style={s.title}>Puntos de servicio</Text>
    <Text style={s.muted}>Busca un punto, consulta su horario y tarifa, y prepara el registro de tu objeto.</Text>
    <Field label="Buscar punto" placeholder="Nombre del punto o zona" value={query} onChangeText={setQuery} autoCorrect={false} returnKeyType="search" />
    <Feedback {...load} />
    {load.error && <Button title="Volver a consultar puntos" secondary onPress={reload} />}
    {matches?.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={"Ver horarios y tarifas de " + item.name}
      onPress={() => { Keyboard.dismiss(); setPointId(item.id); setQuote(null); price.setError(""); }} style={s.card}>
      <View style={s.row}><NavigationIcon name="points" /><Text style={[s.label, s.flex]}>{item.name}</Text></View>
      <Text style={s.muted}>{item.address}</Text>
      <Text style={{ color: c.blue, fontWeight: "700", fontSize: 14 }}>Ver horarios y tarifas →</Text>
    </Pressable>)}
    {points?.length === 0 && <Empty title="No hay puntos publicados" detail="Vuelve a consultar más adelante." />}
    {!!points?.length && matches?.length === 0 && <Empty title="No encontramos ese punto" detail="Prueba con otro nombre o zona." />}
  </Page>;
}
