import Link from "next/link";
import {
  Stethoscope, Users, BarChart3, Heart, Activity,
  MessageCircle, UserCog, Settings, Shield,
  ShieldCheck, Clock, Star, Lock, ArrowRight,
  HeartPulse, ClipboardList, Brain,
} from "lucide-react";

// ── Portal Card ───────────────────────────────────────────────────────────────

interface PortalCardProps {
  avatar: React.ReactNode;
  avatarBg: string;
  title: string;
  titleColor: string;
  description: string;
  features: { icon: React.ReactNode; label: string }[];
  buttonLabel: string;
  buttonClass: string;
  href: string;
}

function PortalCard({
  avatar, avatarBg, title, titleColor, description,
  features, buttonLabel, buttonClass, href,
}: PortalCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-shadow duration-300 p-8 flex flex-col items-center text-center">
      {/* Avatar */}
      <div className={`size-24 rounded-full flex items-center justify-center mb-5 ${avatarBg}`}>
        {avatar}
      </div>

      {/* Title */}
      <h2 className={`text-xl font-bold mb-3 ${titleColor}`}>{title}</h2>

      {/* Description */}
      <p className="text-gray-500 text-sm leading-relaxed mb-6 max-w-xs">{description}</p>

      {/* Features */}
      <ul className="w-full space-y-3 mb-8">
        {features.map(({ icon, label }) => (
          <li key={label} className="flex items-center gap-3 text-sm text-gray-600">
            <span className="text-gray-400">{icon}</span>
            {label}
          </li>
        ))}
      </ul>

      {/* CTA */}
      <Link href={href} className="w-full">
        <button className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl text-white font-semibold text-sm transition-opacity hover:opacity-90 ${buttonClass}`}>
          <ArrowRight className="size-4" />
          {buttonLabel}
        </button>
      </Link>
    </div>
  );
}

// ── Trust Badge ───────────────────────────────────────────────────────────────

function TrustBadge({
  icon, title, description,
}: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 text-blue-500">{icon}</div>
      <div>
        <p className="text-sm font-semibold text-gray-700">{title}</p>
        <p className="text-xs text-gray-500 leading-snug">{description}</p>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        background:
          "radial-gradient(ellipse at 10% 20%, #dbeafe 0%, transparent 50%), radial-gradient(ellipse at 90% 80%, #ede9fe 0%, transparent 50%), #f0f4ff",
      }}
    >
      {/* ── Header ── */}
      <header className="py-6 flex justify-center">
        <div className="flex flex-col items-center gap-1">
          {/* Logo mark */}
          <div className="flex items-center gap-2.5">
            <div className="relative size-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-md">
              <HeartPulse className="size-5 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-gray-800">
              Smart <span className="text-teal-500">Medi</span>
            </span>
          </div>
          <span className="text-xs text-gray-500 font-medium tracking-wide">
            AI-Powered Healthcare Assistant
          </span>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="text-center px-4 pt-10 pb-4">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-800 leading-tight">
          Welcome to Smart Medi Assistant
        </h1>
        <p className="mt-3 text-gray-500 text-base max-w-xl mx-auto">
          Choose your portal to access personalized healthcare solutions
        </p>
      </section>

      {/* ── Portal Cards ── */}
      <section className="flex-1 container max-w-5xl mx-auto px-4 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* Doctor Portal */}
          <PortalCard
            avatarBg="bg-blue-50"
            avatar={
              <div className="flex flex-col items-center gap-1">
                <div className="size-14 rounded-full bg-blue-100 flex items-center justify-center">
                  <Stethoscope className="size-7 text-blue-600" />
                </div>
              </div>
            }
            title="Doctor Portal"
            titleColor="text-blue-600"
            description="Manage your patients, view medical records, and provide better care."
            features={[
              { icon: <Users className="size-4" />, label: "Patient Management" },
              { icon: <ClipboardList className="size-4" />, label: "View Medical Records" },
              { icon: <BarChart3 className="size-4" />, label: "Analytics & Reports" },
            ]}
            buttonLabel="Login as Doctor"
            buttonClass="bg-blue-600 hover:bg-blue-700"
            href="/login"
          />

          {/* Patient Portal */}
          <PortalCard
            avatarBg="bg-teal-50"
            avatar={
              <div className="size-14 rounded-full bg-teal-100 flex items-center justify-center">
                <Heart className="size-7 text-teal-600" />
              </div>
            }
            title="Patient Portal"
            titleColor="text-teal-600"
            description="Access your health information, track vitals, and consult AI assistant."
            features={[
              { icon: <Activity className="size-4" />, label: "Health Dashboard" },
              { icon: <HeartPulse className="size-4" />, label: "Track Vitals & Symptoms" },
              { icon: <Brain className="size-4" />, label: "AI Health Assistant" },
            ]}
            buttonLabel="Login as Patient"
            buttonClass="bg-teal-600 hover:bg-teal-700"
            href="/login"
          />

          {/* Admin Portal */}
          <PortalCard
            avatarBg="bg-violet-50"
            avatar={
              <div className="size-14 rounded-full bg-violet-100 flex items-center justify-center">
                <Shield className="size-7 text-violet-600" />
              </div>
            }
            title="Admin Portal"
            titleColor="text-violet-600"
            description="Manage users, system settings, and ensure smooth operations."
            features={[
              { icon: <UserCog className="size-4" />, label: "User Management" },
              { icon: <Settings className="size-4" />, label: "System Settings" },
              { icon: <ShieldCheck className="size-4" />, label: "Security & Monitoring" },
            ]}
            buttonLabel="Login as Admin"
            buttonClass="bg-violet-600 hover:bg-violet-700"
            href="/login"
          />

        </div>
      </section>

      {/* ── Trust Badges ── */}
      <section className="container max-w-5xl mx-auto px-4 pb-10">
        <div className="bg-white/70 backdrop-blur rounded-2xl shadow-sm px-8 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <TrustBadge
              icon={<ShieldCheck className="size-5" />}
              title="Secure & Private"
              description="Your data is encrypted and protected"
            />
            <TrustBadge
              icon={<MessageCircle className="size-5" />}
              title="AI-Powered Insights"
              description="Get intelligent healthcare recommendations"
            />
            <TrustBadge
              icon={<Clock className="size-5" />}
              title="24/7 Support"
              description="We're here to help anytime"
            />
            <TrustBadge
              icon={<Star className="size-5" />}
              title="Trusted Care"
              description="Reliable. Accurate. Compassionate."
            />
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/50 bg-white/30 backdrop-blur py-5">
        <div className="container max-w-5xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500">
          <span>© {new Date().getFullYear()} Smart Medi Assistant. All rights reserved.</span>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-gray-700 transition-colors">Privacy Policy</a>
            <span className="text-gray-300">|</span>
            <a href="#" className="hover:text-gray-700 transition-colors">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
