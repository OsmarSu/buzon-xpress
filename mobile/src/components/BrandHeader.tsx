import { Pressable, Text, View } from "react-native";
import { router, usePathname } from "expo-router";
import { useSession } from "../auth/SessionProvider";
import { NavigationIcon } from "./NavigationIcon";
import { c, s } from "./theme";

export function BrandHeader() {
  const { user, loading } = useSession();
  const path = usePathname();
  return <View style={{ paddingHorizontal: 16, paddingVertical: 12, flexDirection: "row", alignItems: "center", gap: 8, borderBottomWidth: 1, borderColor: c.border, backgroundColor: c.paper }}>
    <View style={s.flex}><Text numberOfLines={1} adjustsFontSizeToFit minimumFontScale={.8} style={{ color: c.ink, fontSize: 16, fontWeight: "800", letterSpacing: -.5 }}>BUZON <Text style={{ color: c.red }}>Xpress</Text></Text>
      <Text numberOfLines={1} style={{ color: c.muted, fontSize: 8, letterSpacing: .6, fontWeight: "700" }}>CUSTODIA TEMPORAL</Text></View>
    {path !== "/acceso" && !loading && (user
      ? <Pressable accessibilityRole="button" accessibilityLabel="Abrir mi cuenta" onPress={() => router.navigate("/cuenta")} style={{ minWidth: 44, minHeight: 44, justifyContent: "center", alignItems: "center", backgroundColor: c.pale, borderRadius: 14 }}>
        <NavigationIcon name="account" size={22} />
      </Pressable>
      : <Pressable accessibilityRole="button" accessibilityLabel="Iniciar sesión" onPress={() => router.push("/acceso")}
          style={({ pressed }) => ({ paddingHorizontal: 12, minHeight: 44, justifyContent: "center", backgroundColor: c.pale, borderRadius: 12, opacity: pressed ? .7 : 1 })}>
        <Text numberOfLines={1} style={{ color: c.navy, fontSize: 13, fontWeight: "700" }}>Iniciar sesión</Text>
      </Pressable>)}
  </View>;
}
