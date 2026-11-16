import { StyleSheet } from "react-native";
export const c = { ink: "#102342", muted: "#586982", blue: "#0b6bbf", navy: "#0b368c", red: "#bf0f1e", paper: "#ffffff", canvas: "#f3f5f9", border: "#dce4f0", pale: "#eaf2ff", good: "#28644c" };
export const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: c.canvas },
  content: { padding: 20, gap: 18, paddingBottom: 32, width: "100%", maxWidth: 640, alignSelf: "center" },
  title: { color: c.ink, fontSize: 29, fontWeight: "800", letterSpacing: -1, lineHeight: 34 },
  h2: { color: c.ink, fontSize: 20, fontWeight: "700", letterSpacing: -.4 },
  text: { color: c.ink, fontSize: 15, lineHeight: 23 },
  muted: { color: c.muted, fontSize: 14, lineHeight: 22 },
  eyebrow: { color: c.blue, fontSize: 11, fontWeight: "800", letterSpacing: 1.4, textTransform: "uppercase" },
  card: { padding: 20, backgroundColor: c.paper, borderWidth: 1, borderColor: c.border, borderRadius: 20, gap: 14 },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  between: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 12 },
  flex: { flex: 1, minWidth: 0 },
  label: { color: c.ink, fontSize: 14, fontWeight: "700" },
  small: { color: c.muted, fontSize: 12, lineHeight: 19 },
});
