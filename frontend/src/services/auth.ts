import { mutate, request } from "./api";

export type Role = "USUARIO" | "OPERADOR" | "ADMIN" | "AUDITOR" | "REVISOR";

export interface User {
  id: string;
  full_name: string;
  role: Role;
  contact_verified: boolean;
  mfa_enabled: boolean;
}

export interface Session {
  user: User;
  expires_at: string;
}

export interface MfaChallenge {
  mfa_required: true;
  challenge_token: string;
  expires_at: string;
}

export interface MfaStatus {
  enabled: boolean;
  recovery_codes_remaining: number;
}

export interface MfaSetup {
  secret: string;
  otpauth_uri: string;
  expires_at: string;
}

export interface MfaRecoveryCodes {
  enabled: true;
  recovery_codes: string[];
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

export function isMfaChallenge(result: Session | MfaChallenge): result is MfaChallenge {
  return "mfa_required" in result && result.mfa_required === true;
}

export const auth = {
  register: (body: Register) => mutate<User>("/auth/register", body),
  login: (body: Login) => mutate<Session | MfaChallenge>("/auth/login", body),
  verifyMfa: (challenge_token: string, code: string) =>
    mutate<Session>("/auth/mfa/verify", { challenge_token, code }),
  mfaStatus: () => request<MfaStatus>("/auth/mfa"),
  setupMfa: (password: string) => mutate<MfaSetup>("/auth/mfa/setup", { password }),
  confirmMfa: (code: string) => mutate<MfaRecoveryCodes>("/auth/mfa/confirm", { code }),
  disableMfa: (password: string, code: string) =>
    mutate<Resource>("/auth/mfa/disable", { password, code }),
  replaceRecoveryCodes: (password: string, code: string) =>
    mutate<MfaRecoveryCodes>("/auth/mfa/recovery-codes", { password, code }),
  me: () => request<User>("/auth/me"),
  logout: () => mutate<Resource>("/auth/logout"),
  verifyContact: (token: string) => mutate<Resource>("/auth/verify-contact", { token }),
  requestReset: (email: string) => mutate<Resource>("/auth/password-reset/request", { email }),
  completeReset: (token: string, password: string) =>
    mutate<Resource>("/auth/password-reset/complete", { token, password }),
};
