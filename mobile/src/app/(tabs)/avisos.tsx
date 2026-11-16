import { router } from "expo-router";
import { RequireSession } from "../../auth/RequireSession";
import { useSession } from "../../auth/SessionProvider";
import { NoticesScreen } from "../../screens/NoticesScreen";
export default function NoticesRoute() {
  const { user } = useSession();
  return <RequireSession next="/avisos"><NoticesScreen key={user?.id} onOpen={id => router.navigate({ pathname: "/custodias", params: { id } })} /></RequireSession>;
}
