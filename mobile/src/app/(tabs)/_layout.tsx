import { useSafeAreaInsets } from "react-native-safe-area-context";
import { View } from "react-native";
import { Tabs } from "expo-router";
import { useSession } from "../../auth/SessionProvider";
import { NavigationIcon, type NavigationIconName } from "../../components/NavigationIcon";
import { c } from "../../components/theme";

const tabs: { name: string; title: string; icon: NavigationIconName }[] = [
  { name: "index", title: "Seguimiento", icon: "tracking" },
  { name: "custodias", title: "Custodias", icon: "custodies" },
  { name: "puntos", title: "Puntos", icon: "points" },
  { name: "avisos", title: "Avisos", icon: "notices" },
  { name: "cuenta", title: "Cuenta", icon: "account" },
];
export default function TabLayout() {
  const { user } = useSession();
  const insets = useSafeAreaInsets();
  return <Tabs initialRouteName="index" backBehavior="initialRoute" tabBar={user ? undefined : () => null} screenOptions={{
    headerShown: false, tabBarActiveTintColor: c.navy, tabBarInactiveTintColor: c.muted,
    tabBarHideOnKeyboard: true, tabBarStyle: { borderTopColor: c.border, height: 64 + insets.bottom, paddingTop: 7, paddingBottom: Math.max(insets.bottom, 6), backgroundColor: c.paper },
    tabBarIconStyle: { width: 44, height: 28 },
    tabBarLabelStyle: { fontSize: 10, lineHeight: 14, fontWeight: "600", marginHorizontal: 0 }, sceneStyle: { backgroundColor: c.canvas },
  }}>
    {tabs.map(tab => <Tabs.Screen key={tab.name} name={tab.name} options={{
      title: tab.title, tabBarAccessibilityLabel: tab.title, tabBarItemStyle: { flex: tab.name === "index" ? 1.35 : 1 },
      tabBarIcon: ({ focused }) => <View style={{ width: 44, height: 28, borderRadius: 16, backgroundColor: focused ? c.pale : "transparent", alignItems: "center", justifyContent: "center" }}>
        <NavigationIcon name={tab.icon} size={22} color={focused ? c.navy : c.muted} />
      </View>,
    }} />)}
  </Tabs>;
}
