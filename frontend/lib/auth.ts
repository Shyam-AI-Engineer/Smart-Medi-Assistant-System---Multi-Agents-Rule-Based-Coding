const USER_KEY = "medi.user";

export interface AuthUser {
  user_id: string;
  email: string;
  role: "patient" | "doctor" | "nurse" | "admin";
  full_name?: string;
}

// Tokens are stored only in httpOnly cookies (set by /api/auth/* route handlers).
// Only non-sensitive user info is kept in localStorage.
export const auth = {
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
  setSession(opts: { user: AuthUser }) {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(USER_KEY, JSON.stringify(opts.user));
  },
  clear() {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(USER_KEY);
    // Clear httpOnly token cookies via server-side route handler (fire-and-forget)
    void fetch("/api/auth/logout", { method: "POST" }).catch(() => {});
  },
};
