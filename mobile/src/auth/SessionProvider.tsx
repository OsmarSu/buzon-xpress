import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { AppState, Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import * as Crypto from "expo-crypto";
import { BuzonClient } from "../api/client";
import type { MfaChallenge, MobileSession, User } from "../api/types";

const KEY = "buzonxpress.session.v1";
type Saved = { token: string; expires: string };
let previewSession: Saved | null = null;
let storageQueue: Promise<unknown> = Promise.resolve();
function serialized<T>(operation: () => Promise<T>): Promise<T> {
  const result = storageQueue.then(operation);
  storageQueue = result.catch(() => {});
  return result;
}
const storage = {
  read(): Promise<Saved | null> {
    return serialized(async () => {
      if (Platform.OS === "web") return previewSession;
      const raw = await SecureStore.getItemAsync(KEY);
      if (!raw) return null;
      try { return JSON.parse(raw); } catch { await SecureStore.deleteItemAsync(KEY); return null; }
    });
  },
  write(value: Saved) {
    return serialized(async () => {
      if (Platform.OS === "web") { previewSession = value; return; }
      await SecureStore.setItemAsync(KEY, JSON.stringify(value));
    });
  },
  clear() {
    return serialized(async () => {
      previewSession = null;
      if (Platform.OS !== "web") await SecureStore.deleteItemAsync(KEY);
    });
  },
};
interface Context {
  client: BuzonClient; user: User | null; loading: boolean; notice: string;
  signIn: (email: string, password: string) => Promise<MfaChallenge | null>;
  verify: (challenge: string, code: string) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
}
const SessionContext = createContext<Context | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [expires, setExpires] = useState<string | null>(null);
  const generation = useRef(0);
  const [client] = useState(() => new BuzonClient({
    baseUrl: Platform.OS === "web" ? "" : (process.env.EXPO_PUBLIC_API_URL || "https://buzon-xpress.tail1a7cca.ts.net"),
    fetcher: (url, init) => fetch(url, init),
    uuid: () => Crypto.randomUUID(),
  }));
  useEffect(() => {
    client.setUnauthorizedHandler(() => {
      generation.current += 1;
      setUser(null); setExpires(null);
      void storage.clear().catch(() => {});
      setNotice("Tu sesión terminó. Inicia sesión de nuevo.");
    });
    return () => client.setUnauthorizedHandler();
  }, [client]);
  async function complete(session: MobileSession) {
    if (!/^mob_[A-Za-z0-9_-]{43}$/.test(session.access_token) || !Number.isFinite(Date.parse(session.expires_at)) || Date.parse(session.expires_at) <= Date.now()) {
      throw new Error("No se pudo comprobar la sesión recibida.");
    }
    generation.current += 1;
    client.setToken(session.access_token);
    try { await storage.write({ token: session.access_token, expires: session.expires_at }); }
    catch {
      await client.logout().catch(() => {});
      await storage.clear().catch(() => {});
      client.setToken(null); setUser(null); setExpires(null);
      throw new Error("No se pudo guardar la sesión de forma segura. Inténtalo de nuevo.");
    }
    setUser(session.user); setExpires(session.expires_at); setNotice("");
  }
  const refresh = useCallback(async () => {
    const currentGeneration = generation.current;
    const saved = await storage.read();
    if (currentGeneration !== generation.current) return;
    if (!saved || !/^mob_[A-Za-z0-9_-]{43}$/.test(saved.token) || !Number.isFinite(Date.parse(saved.expires)) || Date.parse(saved.expires) <= Date.now()) {
      if (saved) await storage.clear();
      if (currentGeneration === generation.current) { client.setToken(null); setUser(null); setExpires(null); }
      return;
    }
    client.setToken(saved.token);
    const current = await client.me();
    if (currentGeneration !== generation.current) return;
    setUser(current); setExpires(saved.expires); setNotice("");
  }, [client]);
  useEffect(() => {
    let mounted = true;
    void refresh().catch(e => { if (mounted) setNotice(e instanceof Error ? e.message : "No se pudo restaurar la sesión."); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [refresh]);
  useEffect(() => {
    const listener = AppState.addEventListener("change", state => {
      if (state === "active") void refresh().catch(e => setNotice(e instanceof Error ? e.message : "Vuelve a consultar tu cuenta."));
    });
    const timer = expires ? setTimeout(() => {
      generation.current += 1;
      client.setToken(null); setUser(null); setExpires(null); void storage.clear().catch(() => {});
      setNotice("Tu sesión terminó. Inicia sesión de nuevo.");
    }, Math.max(0, Date.parse(expires) - Date.now())) : undefined;
    return () => { listener.remove(); if (timer) clearTimeout(timer); };
  }, [client, expires, refresh]);
  async function signIn(email: string, password: string) {
    const result = await client.login(email.trim().toLowerCase(), password);
    if ("mfa_required" in result) return result;
    await complete(result); return null;
  }
  async function verify(challenge: string, code: string) { await complete(await client.verifyMfa(challenge, code.trim())); }
  async function signOut() {
    generation.current += 1;
    let failed = false;
    try { await client.logout(); } catch { failed = true; }
    try { await storage.clear(); }
    catch { if (failed) throw new Error("No se pudo cerrar la sesión. Comprueba tu conexión e inténtalo de nuevo."); }
    client.setToken(null); setUser(null); setExpires(null);
    setNotice(failed ? "La sesión se quitó del teléfono. No se pudo confirmar el cierre en el servicio." : "Sesión cerrada.");
  }
  return <SessionContext.Provider value={{ client, user, loading, notice, signIn, verify, signOut, refresh }}>{children}</SessionContext.Provider>;
}
export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error("SessionProvider is required.");
  return value;
}
