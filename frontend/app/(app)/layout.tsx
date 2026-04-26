"use client";

import { Sidebar, MobileTopbar } from "@/components/layout/Sidebar";
import { useRequireAuth } from "@/hooks/useAuth";
import { FullPageLoader } from "@/components/ui/Loader";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { ready } = useRequireAuth();

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
