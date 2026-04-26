"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";

export function useAuth() {
  const { user, hydrated, hydrate, signIn, signOut } = useAuthStore();

  useEffect(() => {
    if (!hydrated) hydrate();
  }, [hydrated, hydrate]);

  return { user, hydrated, signIn, signOut, isAuthenticated: Boolean(user) };
}

export function useRequireAuth() {
  const router = useRouter();
  const { user, hydrated } = useAuth();

  useEffect(() => {
    if (hydrated && !user) {
      const next =
        typeof window !== "undefined"
          ? encodeURIComponent(window.location.pathname)
          : "";
      router.replace(`/login${next ? `?next=${next}` : ""}`);
    }
  }, [hydrated, user, router]);

  return { user, hydrated, ready: hydrated && Boolean(user) };
}
