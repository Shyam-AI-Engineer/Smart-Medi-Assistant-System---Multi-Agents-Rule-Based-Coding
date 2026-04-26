"use client";

import { create } from "zustand";
import { auth, type AuthUser } from "@/lib/auth";

interface AuthState {
  user: AuthUser | null;
  hydrated: boolean;
  hydrate: () => void;
  signIn: (token: string, refreshToken: string | undefined, user: AuthUser) => void;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  hydrated: false,
  hydrate: () => set({ user: auth.getUser(), hydrated: true }),
  signIn: (token, refreshToken, user) => {
    auth.setSession({ accessToken: token, refreshToken, user });
    set({ user });
  },
  signOut: () => {
    auth.clear();
    set({ user: null });
  },
}));
