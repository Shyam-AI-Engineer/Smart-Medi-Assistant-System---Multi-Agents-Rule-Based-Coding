"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Stethoscope, Heart, Shield, ArrowRight, ArrowLeft,
  Mail, Lock, AlertCircle, HeartPulse, Users,
  BarChart3, ClipboardList, Activity, Brain,
  UserCog, Settings, ShieldCheck, Clock, Star,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { endpoints, getApiErrorMessage } from "@/lib/api";

// ── Portal definitions ────────────────────────────────────────────────────────

const PORTALS = [
  {
    id: "patient",
    title: "Patient Portal",
    description: "Access your health information, track vitals, and consult AI assistant.",
    icon: Heart,
    avatarBg: "bg-teal-100",
    avatarColor: "text-teal-600",
    titleColor: "text-teal-600",
    btnClass: "bg-teal-600 hover:bg-teal-700",
    cardBorder: "hover:border-teal-300",
    features: [
      { icon: Activity, label: "Health Dashboard" },
      { icon: HeartPulse, label: "Track Vitals & Symptoms" },
      { icon: Brain, label: "AI Health Assistant" },
    ],
  },
  {
    id: "doctor",
    title: "Doctor Portal",
    description: "Manage your patients, view medical records, and provide better care.",
    icon: Stethoscope,
    avatarBg: "bg-blue-100",
    avatarColor: "text-blue-600",
    titleColor: "text-blue-600",
    btnClass: "bg-blue-600 hover:bg-blue-700",
    cardBorder: "hover:border-blue-300",
    features: [
      { icon: Users, label: "Patient Management" },
      { icon: ClipboardList, label: "View Medical Records" },
      { icon: BarChart3, label: "Analytics & Reports" },
    ],
  },
  {
    id: "admin",
    title: "Admin Portal",
    description: "Manage users, system settings, and ensure smooth operations.",
    icon: Shield,
    avatarBg: "bg-violet-100",
    avatarColor: "text-violet-600",
    titleColor: "text-violet-600",
    btnClass: "bg-violet-600 hover:bg-violet-700",
    cardBorder: "hover:border-violet-300",
    features: [
      { icon: UserCog, label: "User Management" },
      { icon: Settings, label: "System Settings" },
      { icon: ShieldCheck, label: "Security & Monitoring" },
    ],
  },
] as const;

type PortalId = (typeof PORTALS)[number]["id"];

const BADGES = [
  { icon: ShieldCheck, title: "Secure & Private", desc: "Data encrypted and protected" },
  { icon: Brain, title: "AI-Powered Insights", desc: "Intelligent healthcare recommendations" },
  { icon: Clock, title: "24/7 Support", desc: "Here to help anytime" },
  { icon: Star, title: "Trusted Care", desc: "Reliable. Accurate. Compassionate." },
];

// ── Page ──────────────────────────────────────────────────────────────────────

function LoginContent() {
  const router = useRouter();
  const search = useSearchParams();
  const { signIn, isAuthenticated, hydrated, user } = useAuth();

  const nextParam = search.get("next");
  const [selectedPortal, setSelectedPortal] = useState<PortalId | null>(null);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (hydrated && isAuthenticated && user) {
      const dest =
        nextParam ||
        (user.role === "doctor"
          ? "/doctor/dashboard"
          : user.role === "admin"
          ? "/admin/dashboard"
          : "/dashboard");
      router.replace(dest);
    }
  }, [hydrated, isAuthenticated, user, router, nextParam]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data =
        mode === "login"
          ? await endpoints.login({ email, password })
          : await endpoints.register({ email, password, full_name: fullName });

      signIn({
        user_id: data.user_id,
        email: data.email,
        role: data.role,
        full_name: data.full_name ?? undefined,
      });

      const dest =
        nextParam ||
        (data.role === "doctor"
          ? "/doctor/dashboard"
          : data.role === "admin"
          ? "/admin/dashboard"
          : "/dashboard");
      router.replace(dest);
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to sign in. Check your credentials."));
    } finally {
      setSubmitting(false);
    }
  }

  const portal = PORTALS.find((p) => p.id === selectedPortal);
  const bgStyle = {
    background:
      "radial-gradient(ellipse at 10% 20%, #dbeafe 0%, transparent 50%), radial-gradient(ellipse at 90% 80%, #ede9fe 0%, transparent 50%), #f0f4ff",
  };

  // ── Portal selection ──────────────────────────────────────────────────────

  if (!selectedPortal) {
    return (
      <div className="min-h-screen flex flex-col" style={bgStyle}>
        {/* Header */}
        <header className="py-6 flex justify-center">
          <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-2.5">
              <div className="size-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-md">
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

        {/* Hero */}
        <section className="text-center px-4 pt-8 pb-4">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800">
            Welcome to Smart Medi Assistant
          </h1>
          <p className="mt-3 text-gray-500 text-base max-w-xl mx-auto">
            Choose your portal to access personalized healthcare solutions
          </p>
        </section>

        {/* Cards */}
        <section className="flex-1 mx-auto w-full max-w-5xl px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PORTALS.map((p) => {
              const Icon = p.icon;
              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedPortal(p.id)}
                  className={`bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 p-8 flex flex-col items-center text-center border-2 border-transparent ${p.cardBorder} cursor-pointer`}
                >
                  <div className={`size-24 rounded-full flex items-center justify-center mb-5 ${p.avatarBg}`}>
                    <Icon className={`size-10 ${p.avatarColor}`} />
                  </div>
                  <h2 className={`text-xl font-bold mb-3 ${p.titleColor}`}>{p.title}</h2>
                  <p className="text-gray-500 text-sm leading-relaxed mb-6 max-w-xs">{p.description}</p>
                  <ul className="w-full space-y-3 mb-8">
                    {p.features.map(({ icon: FIcon, label }) => (
                      <li key={label} className="flex items-center gap-3 text-sm text-gray-600">
                        <FIcon className="size-4 text-gray-400 shrink-0" />
                        {label}
                      </li>
                    ))}
                  </ul>
                  <button
                    className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl text-white font-semibold text-sm ${p.btnClass}`}
                  >
                    <ArrowRight className="size-4" />
                    Login as {p.id.charAt(0).toUpperCase() + p.id.slice(1)}
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        {/* Trust badges */}
        <section className="mx-auto w-full max-w-5xl px-4 pb-8">
          <div className="bg-white/70 backdrop-blur rounded-2xl shadow-sm px-8 py-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {BADGES.map(({ icon: BIcon, title, desc }) => (
                <div key={title} className="flex items-start gap-3">
                  <BIcon className="size-5 text-blue-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-gray-700">{title}</p>
                    <p className="text-xs text-gray-500 leading-snug">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/50 bg-white/30 py-4">
          <div className="mx-auto w-full max-w-5xl px-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500">
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

  // ── Login form ────────────────────────────────────────────────────────────

  const PortalIcon = portal!.icon;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={bgStyle}>
      <div className="w-full max-w-md">
        {/* Back */}
        <button
          onClick={() => { setSelectedPortal(null); setError(null); }}
          className="mb-6 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="size-4" />
          Back to portals
        </button>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Portal badge */}
          <div className="flex flex-col items-center mb-8">
            <div className={`size-16 rounded-full flex items-center justify-center mb-3 ${portal!.avatarBg}`}>
              <PortalIcon className={`size-8 ${portal!.avatarColor}`} />
            </div>
            <h1 className={`text-xl font-bold ${portal!.titleColor}`}>{portal!.title}</h1>
            <p className="text-sm text-gray-500 mt-1">
              {mode === "login" ? "Sign in to access your dashboard." : "Create your account."}
            </p>
          </div>

          {/* Sign in / Register toggle */}
          <div className="flex rounded-xl overflow-hidden border border-gray-200 mb-6">
            <button
              onClick={() => { setMode("login"); setError(null); }}
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${mode === "login" ? "bg-gray-900 text-white" : "text-gray-500 hover:text-gray-700"}`}
            >
              Sign in
            </button>
            <button
              onClick={() => { setMode("register"); setError(null); }}
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${mode === "register" ? "bg-gray-900 text-white" : "text-gray-500 hover:text-gray-700"}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-gray-50"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-gray-50"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-gray-50"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 px-3 py-2.5 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
                <AlertCircle className="size-4 mt-0.5 shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className={`w-full py-3 rounded-xl text-white font-semibold text-sm transition-opacity disabled:opacity-60 ${portal!.btnClass}`}
            >
              {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}
