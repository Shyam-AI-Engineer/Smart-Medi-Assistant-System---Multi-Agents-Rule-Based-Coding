"use client";

import { DoctorSidebar } from "@/components/layout/DoctorSidebar";
import { useRequireRole } from "@/hooks/useAuth";
import { FullPageLoader } from "@/components/ui/Loader";

export default function DoctorLayout({ children }: { children: React.ReactNode }) {
  const { ready } = useRequireRole("doctor", "admin");

  if (!ready) return <FullPageLoader />;

  return (
    <div className="min-h-screen flex bg-bg">
      <DoctorSidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
