"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AdminSidebar, AdminMobileTopbar } from "@/components/layout/AdminSidebar";
import { useAuth } from "@/hooks/useAuth";
import { FullPageLoader } from "@/components/ui/Loader";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, hydrated } = useAuth();

  useEffect(() => {
    if (!hydrated) return;
    if (!user || user.role !== "admin") {
      router.replace("/login");
    }
  }, [hydrated, user, router]);

  const ready = hydrated && user?.role === "admin";
  if (!ready) return <FullPageLoader />;

  return (
    <div className="min-h-screen flex bg-bg">
      <AdminSidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <AdminMobileTopbar />
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
