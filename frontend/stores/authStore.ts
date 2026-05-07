"use client";

import { create } from "zustand";
import { auth, type AuthUser } from "@/lib/auth";

interface AuthState {
  user: AuthUser | null;
  hydrated: boolean;
  hydrate: () => void;
  signIn: (user: AuthUser) => void;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  hydrated: false,
  hydrate: () => set({ user: auth.getUser(), hydrated: true }),
  signIn: (user) => {
    auth.setSession({ user });
    set({ user });
  },
  signOut: () => {
    auth.clear();
    set({ user: null });
  },
}));
