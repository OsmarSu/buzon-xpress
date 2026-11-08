import { mutate, request } from "./api";

export type Role = "USUARIO" | "OPERADOR" | "ADMIN" | "AUDITOR";

export interface User {
  id: string;
  full_name: string;
  role: Role;
  contact_verified: boolean;
}

export interface Session {
  user: User;
  expires_at: string;
}

export interface Login {
  email: string;
  password: string;
}

export interface Register extends Login {
  full_name: string;
  phone?: string;
}

export interface Resource {
  id: string;
  state?: string;
}

export const auth = {
  register: (body: Register) => mutate<User>("/auth/register", body),
  login: (body: Login) => mutate<Session>("/auth/login", body),
  me: () => request<User>("/auth/me"),
  logout: () => mutate<Resource>("/auth/logout"),
  verifyContact: (token: string) => mutate<Resource>("/auth/verify-contact", { token }),
  requestReset: (email: string) => mutate<Resource>("/auth/password-reset/request", { email }),
  completeReset: (token: string, password: string) =>
    mutate<Resource>("/auth/password-reset/complete", { token, password }),
};
