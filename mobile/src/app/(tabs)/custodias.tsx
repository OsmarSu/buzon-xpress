import { useCallback, useMemo } from "react";
import { router, useLocalSearchParams } from "expo-router";
import { RequireSession } from "../../auth/RequireSession";
import { useSession } from "../../auth/SessionProvider";
import { CustodiesScreen } from "../../screens/CustodiesScreen";
import { custodyId, registrationDraft } from "../../navigation/paths";
export default function CustodiesRoute() {
  const { id, point, size, hours, crear } = useLocalSearchParams<{ id?: string; point?: string; size?: string; hours?: string; crear?: string }>();
  const { user } = useSession();
  const draft = useMemo(() => crear === "1" ? registrationDraft(point, size, hours) : undefined, [crear, point, size, hours]);
  const consumeDraft = useCallback(() => router.setParams({ crear: undefined, point: undefined, size: undefined, hours: undefined }), []);
  return <RequireSession next="/custodias"><CustodiesScreen key={user?.id} openId={custodyId(id)} onCloseLink={() => router.setParams({ id: undefined })}
    draft={draft} onConsumeDraft={consumeDraft} /></RequireSession>;
}
