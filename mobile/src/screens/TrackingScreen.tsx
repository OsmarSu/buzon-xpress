import { useState } from "react";
import { Text, View } from "react-native";
import { useSession } from "../auth/SessionProvider";
import { Button, Feedback, Field, Page, useAction } from "../components/ui";
import { NavigationIcon } from "../components/NavigationIcon";
import { OpeningHours } from "../components/OpeningHours";
import { c, s } from "../components/theme";
import type { Tracking } from "../api/types";

const stateLabels = { PENDIENTE: "Pendiente de recepción", RECIBIDA: "En custodia", FINALIZADA: "Finalizada" };
export function TrackingScreen() {
  const { client, notice } = useSession();
  const [reference, setReference] = useState("");
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const search = useAction();
  async function lookup() {
    if (!reference.trim()) throw new Error("Ingresa el código de paquete que te compartieron.");
    setTracking(null);
    setTracking(await client.tracking(reference.trim()));
  }
  return <Page>
    <View style={{ gap: 12 }}>
      <View style={{ backgroundColor: c.pale, borderRadius: 16, padding: 14, alignSelf: "flex-start" }}><NavigationIcon name="tracking" size={28} /></View>
      <Text accessibilityRole="header" style={s.title}>Consultar seguimiento</Text>
      <Text style={s.muted}>Ingresa el código de paquete que te compartieron al registrar la custodia.</Text>
    </View>
    {!!notice && <Feedback message={notice} />}
    <View style={s.card}>
      <Field required label="Código de Paquete" placeholder="Pega el código de paquete" value={reference} editable={!search.busy}
        autoCapitalize="none" autoCorrect={false} autoComplete="off" maxLength={180} returnKeyType="search"
        onChangeText={value => { setReference(value); setTracking(null); search.setError(""); }}
        onSubmitEditing={() => void search.run(lookup)} />
      <Button title="Consultar estado" busy={search.busy} onPress={() => void search.run(lookup)} />
      <Feedback {...search} />
    </View>
    {tracking && <View style={s.card}>
      <Text style={s.eyebrow}>ESTADO DE TU CUSTODIA</Text>
      <Text accessibilityRole="header" style={s.h2}>{stateLabels[tracking.state]}</Text>
      <View style={{ height: 1, backgroundColor: c.border }} />
      <Text style={s.label}>{tracking.point_name}</Text>
      <OpeningHours hours={tracking.opening_hours} />
    </View>}
  </Page>;
}
