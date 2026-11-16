import { Text, View } from "react-native";
import { c, s } from "./theme";

export function OpeningHours({ hours }: { hours: Record<string, unknown> }) {
  return <View style={{ gap: 4 }}>{Object.entries(hours).map(([day, value]) => <View key={day} style={s.between}>
    <Text style={[s.small, { flex: 1 }]}>{day}</Text><Text style={[s.small, { color: c.ink, flex: 1, textAlign: "right" }]}>{typeof value === "string" ? value : "Consulta al personal"}</Text>
  </View>)}</View>;
}
