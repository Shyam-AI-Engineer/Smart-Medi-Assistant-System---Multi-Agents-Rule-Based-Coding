"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar, MobileTopbar } from "@/components/layout/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { FullPageLoader } from "@/components/ui/Loader";
import { useOnboarding } from "@/hooks/useOnboarding";
import { useMyPatientProfile } from "@/hooks/useVitals";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, hydrated } = useAuth();
  const { showWizard, completeWizard } = useOnboarding();
  const { data: profile } = useMyPatientProfile();

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role === "doctor") {
      router.replace("/doctor/dashboard");
      return;
    }
    if (user.role === "admin") {
      router.replace("/admin/dashboard");
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
      {showWizard && (
        <OnboardingWizard profile={profile ?? null} onComplete={completeWizard} />
      )}
    </div>
  );
}
