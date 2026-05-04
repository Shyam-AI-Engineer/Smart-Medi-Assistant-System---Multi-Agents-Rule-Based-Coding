const TOKEN_KEY = "medi.access_token";
const REFRESH_KEY = "medi.refresh_token";
const USER_KEY = "medi.user";

export interface AuthUser {
  user_id: string;
  email: string;
  role: "patient" | "doctor" | "nurse" | "admin";
  full_name?: string;
}

export const auth = {
  getToken(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(TOKEN_KEY);
  },
  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_KEY);
  },
  getUser(): AuthUser | null {
    if (typeof window === "undefined") return null;
    const raw = window.localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  },
  setSession(opts: { accessToken: string; refreshToken?: string; user: AuthUser }) {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(TOKEN_KEY, opts.accessToken);
    if (opts.refreshToken) window.localStorage.setItem(REFRESH_KEY, opts.refreshToken);
    window.localStorage.setItem(USER_KEY, JSON.stringify(opts.user));
  },
  clear() {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
    window.localStorage.removeItem(USER_KEY);
  },
  isAuthenticated(): boolean {
    return Boolean(this.getToken());
  },
};
