import { KeyboardProvider } from "react-native-keyboard-controller";
import { ActivityIndicator, Text, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SessionProvider, useSession } from "../auth/SessionProvider";
import { BrandHeader } from "../components/BrandHeader";
import { StartupSplash } from "../components/StartupSplash";
import { c, s } from "../components/theme";

function RootNavigation() {
  const { loading } = useSession();
  return <SafeAreaView style={{ flex: 1, backgroundColor: c.paper }} edges={["top", "left", "right"]}>
    <StatusBar style="dark" /><BrandHeader />
    {loading ? <View style={{ flex: 1, justifyContent: "center", alignItems: "center", gap: 14, backgroundColor: c.canvas }}>
      <ActivityIndicator color={c.blue} size="large" /><Text style={s.muted}>Preparando tu espacio…</Text>
    </View> : <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: c.canvas }, animation: "fade" }}>
      <Stack.Screen name="(tabs)" /><Stack.Screen name="acceso" /><Stack.Screen name="+not-found" />
    </Stack>}
  </SafeAreaView>;
}
export default function RootLayout() {
  return <SafeAreaProvider>
    <KeyboardProvider statusBarTranslucent navigationBarTranslucent preserveEdgeToEdge preload={false}>
      <SessionProvider>
        <View style={{ flex: 1 }}>
          <RootNavigation />
          <StartupSplash />
        </View>
      </SessionProvider>
    </KeyboardProvider>
  </SafeAreaProvider>;
}
