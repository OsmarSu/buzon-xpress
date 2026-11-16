import { Redirect, router, useLocalSearchParams } from "expo-router";
import { AuthScreen } from "../auth/AuthScreen";
import { useSession } from "../auth/SessionProvider";
import { safeReturnPath } from "../navigation/paths";
export default function AccessRoute() {
  const { next, modo } = useLocalSearchParams<{ next?: string; modo?: string }>();
  const { user } = useSession();
  const destination = safeReturnPath(next);
  if (user) return <Redirect href={destination} />;
  return <AuthScreen key={modo} initialMode={modo === "register" ? "register" : modo === "reset" ? "reset" : "login"}
    onClose={() => router.replace("/")} onSuccess={() => router.replace(destination)} />;
}
