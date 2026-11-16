import { RequireSession } from "../../auth/RequireSession";
import { AccountScreen } from "../../screens/AccountScreen";
export default function AccountRoute() {
  return <RequireSession next="/cuenta"><AccountScreen /></RequireSession>;
}
