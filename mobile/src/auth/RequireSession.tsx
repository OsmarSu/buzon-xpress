import { type ReactNode } from "react";
import { Redirect } from "expo-router";
import { useSession } from "./SessionProvider";
import type { PersonalPath } from "../navigation/paths";

export function RequireSession({ children, next }: { children: ReactNode; next: PersonalPath }) {
  const { user, loading } = useSession();
  if (loading) return null;
  if (!user) return <Redirect href={{ pathname: "/acceso", params: { next } }} />;
  return children;
}
