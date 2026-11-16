import { RequireSession } from "../../auth/RequireSession";
import { PointsScreen } from "../../screens/PointsScreen";
export default function PointsRoute() {
  return <RequireSession next="/puntos"><PointsScreen /></RequireSession>;
}
