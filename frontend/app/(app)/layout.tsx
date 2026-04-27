"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar, MobileTopbar } from "@/components/layout/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { FullPageLoader } from "@/components/ui/Loader";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, hydrated } = useAuth();

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role === "doctor" || user.role === "admin") {
      router.replace("/doctor/dashboard");
    }
  }, [hydrated, user, router]);

  const ready = hydrated && Boolean(user) && user?.role === "patient";
  if (!ready) return <FullPageLoader />;

  return (
    <div className="min-h-screen flex bg-bg">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <MobileTopbar />
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
