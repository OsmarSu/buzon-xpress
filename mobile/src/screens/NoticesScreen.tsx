import { useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Text, View } from "react-native";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useSession } from "../auth/SessionProvider";
import { Button, Empty, Feedback, Page, useAction } from "../components/ui";
import { c, s } from "../components/theme";
import { dateLabel, type Notice } from "../api/types";

const custodyLink = /\/#custodia=([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})/i;
export function NoticesScreen({ onOpen }: { onOpen: (id: string) => void }) {
  const { client } = useSession();
  const [items, setItems] = useState<Notice[] | null>(null);
  const task = useAction();
  const { run } = task;
  const reload = useCallback(() => { void run(async () => setItems(await client.notices())); }, [client, run]);
  useFocusEffect(reload);
  return <Page><Text style={s.eyebrow}>AL DÍA CON TUS OBJETOS</Text><Text accessibilityRole="header" style={s.title}>Tus avisos</Text><Text style={s.muted}>Recepciones, plazos y retiros en una misma bandeja.</Text>
    <Button title="Actualizar avisos" secondary busy={task.busy} onPress={reload} /><Feedback {...task} />
    {items?.length === 0 && <Empty title="Todavía no tienes avisos" detail="Las novedades de tus custodias aparecerán aquí." />}
    {items?.map(item => {
      const linked = item.body.match(custodyLink);
      const body = linked && item.body.startsWith("Consulta el detalle privado de la custodia en ")
        ? "Abre el detalle de esta custodia para consultar su estado y movimientos."
        : item.body.replace(custodyLink, "").replace(/\s+([.,;:])/g, "$1").trim();
      return <View key={item.id} style={[s.card, !item.read_at && { borderLeftWidth: 4, borderLeftColor: c.blue }]}>
        <View style={s.row}><Ionicons accessible={false} accessibilityElementsHidden importantForAccessibility="no-hide-descendants" aria-hidden={true} name={item.read_at ? "mail-open-outline" : "mail-unread-outline"} size={22} color={c.blue} />
          <Text style={[s.label, s.flex]}>{item.subject}</Text></View>
        <Text style={s.small}>{dateLabel(item.created_at)} · {item.read_at ? "Leído" : "Sin leer"}</Text>
        <Text style={s.text}>{body}</Text>
        {linked && <Button title="Abrir custodia" secondary onPress={() => onOpen(linked[1])} />}
        {!item.read_at && <Button title="Marcar como leído" secondary busy={task.busy} onPress={() => void task.run(async () => { await client.readNotice(item.id); setItems(await client.notices()); })} />}
      </View>;
    })}
  </Page>;
}
