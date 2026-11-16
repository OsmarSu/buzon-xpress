import { Link } from "expo-router";
import { Text } from "react-native";
import { Page } from "../components/ui";
import { s, c } from "../components/theme";
export default function NotFound() {
  return <Page><Text accessibilityRole="header" style={s.title}>Esta pantalla no está disponible</Text>
    <Text style={s.muted}>Vuelve al inicio para consultar tus custodias o encontrar un punto de servicio.</Text>
    <Link href="/" replace style={{ color: c.navy, fontWeight: "700", paddingVertical: 15 }}>Volver al inicio</Link>
  </Page>;
}
