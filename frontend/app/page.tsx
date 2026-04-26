import Link from "next/link";
import { ArrowRight, Stethoscope, Activity, MessagesSquare, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-bg">
      <header className="border-b border-border bg-bg-elevated/80 backdrop-blur sticky top-0 z-30">
        <div className="container flex h-16 items-center justify-between">
          <Logo />
          <nav className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/login?mode=register">
              <Button size="sm">Get started</Button>
            </Link>
          </nav>
        </div>
      </header>

      <section className="container py-20 md:py-28">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium text-brand-700 bg-brand-50 border border-brand-100 rounded-full">
            <ShieldCheck className="size-3.5" /> HIPAA-ready architecture
          </span>
          <h1 className="mt-6 text-4xl md:text-5xl font-semibold tracking-tight text-ink leading-[1.1]">
            Clinical-grade AI assistance, built for modern care teams.
          </h1>
          <p className="mt-5 text-lg text-ink-muted leading-relaxed">
            MediAssist combines real-time vitals monitoring, RAG-powered medical chat,
            and intelligent triage in one secure platform — so clinicians can focus on patients.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <Link href="/login">
              <Button size="lg">
                Open dashboard <ArrowRight className="size-4" />
              </Button>
            </Link>
            <Link href="/chat">
              <Button size="lg" variant="secondary">Try AI chat</Button>
            </Link>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-5">
          <FeatureCard
            icon={<Activity className="size-5" />}
            title="Real-time vitals"
            description="Stream measurements, detect anomalies, and surface trends — improving, stable, or worsening — at a glance."
          />
          <FeatureCard
            icon={<MessagesSquare className="size-5" />}
            title="Clinical AI chat"
            description="Ground answers in your medical knowledge base via RAG. Every response is sourced and auditable."
          />
          <FeatureCard
            icon={<Stethoscope className="size-5" />}
            title="Smart triage"
            description="Severity scoring and escalation guidance, calibrated against medical thresholds — never guesswork."
          />
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="container py-6 flex items-center justify-between text-sm text-ink-subtle">
          <span>© {new Date().getFullYear()} MediAssist</span>
          <span>Built with Next.js · FastAPI · Euri</span>
        </div>
      </footer>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="surface p-6 transition-shadow hover:shadow-elevated">
      <div className="size-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
        {icon}
      </div>
      <h3 className="mt-4 text-base font-semibold text-ink">{title}</h3>
      <p className="mt-2 text-sm text-ink-muted leading-relaxed">{description}</p>
    </div>
  );
}
