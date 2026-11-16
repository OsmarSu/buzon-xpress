import { router } from "expo-router";
import { useState } from "react";
import { Linking, Text, View } from "react-native";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useSession } from "../auth/SessionProvider";
import { Button, Feedback, Page, useAction } from "../components/ui";
import { c, s } from "../components/theme";

export function AccountScreen() {
  const { user, refresh, signOut } = useSession();
  const [showId, setShowId] = useState(false);
  const task = useAction();
  if (!user) return null;
  return <Page><Text style={s.eyebrow}>TU ESPACIO PERSONAL</Text><Text accessibilityRole="header" style={s.title}>Mi cuenta</Text>
    <View style={s.card}><View style={[s.row, { alignItems: "flex-start" }]}>
      <View style={{ backgroundColor: c.pale, borderRadius: 18, padding: 15 }}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="person-outline" size={30} color={c.blue} /></View>
      <View style={s.flex}><Text accessibilityRole="header" style={s.h2}>{user.full_name}</Text><Text style={s.muted}>{({ USUARIO: "Cuenta personal", OPERADOR: "Operador", ADMIN: "Administración", AUDITOR: "Auditoría" })[user.role]}</Text></View>
    </View><Text style={{ color: user.contact_verified ? c.good : c.muted, fontWeight: "600" }}>{user.contact_verified ? "Contacto comprobado" : "Contacto pendiente de verificación"}</Text>
      {!user.contact_verified && <><Text style={s.muted}>Abre el enlace recibido por correo para verificar tu contacto y habilitar el registro de objetos.</Text>
        <Button title="Ya verifiqué mi correo" secondary busy={task.busy} onPress={() => void task.run(refresh)} /></>}
    </View>
    <View style={s.card}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name="shield-checkmark-outline" size={27} color={c.blue} /><Text accessibilityRole="header" style={s.h2}>Seguridad de acceso</Text>
      <Text style={s.muted}>{user.mfa_enabled ? "Tu verificación en dos pasos está activa. Conserva tus códigos de recuperación en un lugar privado." : "Puedes activar la verificación en dos pasos para proteger tus próximos accesos."}</Text>
      <Button title="Gestionar seguridad en el sitio web" secondary onPress={() => void task.run(async () => { await Linking.openURL("https://buzon-xpress.surge.sh/cuenta"); })} />
    </View>
    <View style={s.card}><Text style={s.label}>Identificador de mi cuenta</Text><Text style={s.small}>Compártelo solo con personal autorizado para comprobar tu contacto o asignarte funciones.</Text>
      <Button title={showId ? "Ocultar identificador" : "Ver mi identificador"} secondary onPress={() => setShowId(!showId)} />
      {showId && <Text selectable style={s.small}>{user.id}</Text>}
    </View>
    <Feedback {...task} /><Button title="Cerrar sesión" secondary busy={task.busy} onPress={() => void task.run(async () => { await signOut(); router.replace("/"); })} />
  </Page>;
}
