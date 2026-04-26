"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, User, AlertCircle, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { endpoints, getApiErrorMessage } from "@/lib/api";

function LoginContent() {
  const router = useRouter();
  const search = useSearchParams();
  const { signIn, isAuthenticated, hydrated } = useAuth();

  const initialMode = search.get("mode") === "register" ? "register" : "login";
  const next = search.get("next") || "/dashboard";

  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (hydrated && isAuthenticated) router.replace(next);
  }, [hydrated, isAuthenticated, router, next]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data =
        mode === "login"
          ? await endpoints.login({ email, password })
          : await endpoints.register({ email, password, full_name: fullName });

      signIn(data.access_token, data.refresh_token, {
        user_id: data.user_id,
        email: data.email,
        role: data.role,
        full_name: data.full_name,
      });
      router.replace(next);
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to sign in. Check your credentials."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-bg">
      {/* Left: form */}
      <div className="flex flex-col justify-center px-6 py-12 lg:px-16">
        <div className="mx-auto w-full max-w-sm">
          <Link href="/" aria-label="Home">
            <Logo />
          </Link>

          <div className="mt-10">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="mt-2 text-sm text-ink-muted">
              {mode === "login"
                ? "Sign in to access your patient dashboard."
                : "Start monitoring vitals and chatting with the AI in minutes."}
            </p>
          </div>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            {mode === "register" && (
              <Input
                name="full_name"
                label="Full name"
                placeholder="Jane Doe"
                prefix={<User className="size-4" />}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                autoComplete="name"
              />
            )}
            <Input
              name="email"
              type="email"
              label="Email"
              placeholder="you@hospital.com"
              prefix={<Mail className="size-4" />}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
            <Input
              name="password"
              type="password"
              label="Password"
              placeholder="••••••••"
              prefix={<Lock className="size-4" />}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              hint={mode === "register" ? "At least 8 characters." : undefined}
            />

            {error && (
              <div className="flex items-start gap-2 px-3 py-2.5 rounded-md bg-danger-50 border border-danger-100 text-sm text-danger-700">
                <AlertCircle className="size-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" loading={submitting} fullWidth size="lg">
              {mode === "login" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-ink-muted text-center">
            {mode === "login" ? (
              <>
                New here?{" "}
                <button
                  type="button"
                  className="font-medium text-brand-600 hover:text-brand-700"
                  onClick={() => setMode("register")}
                >
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already registered?{" "}
                <button
                  type="button"
                  className="font-medium text-brand-600 hover:text-brand-700"
                  onClick={() => setMode("login")}
                >
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>
      </div>

      {/* Right: hero panel */}
      <div className="hidden lg:flex relative overflow-hidden bg-gradient-to-br from-brand-600 via-brand-700 to-brand-900">
        <div className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, white 0, transparent 50%), radial-gradient(circle at 80% 60%, white 0, transparent 50%)",
          }}
        />
        <div className="relative flex flex-col justify-between p-12 text-white w-full">
          <div className="inline-flex w-fit items-center gap-2 px-3 py-1 text-xs font-medium bg-white/10 border border-white/20 rounded-full backdrop-blur">
            <ShieldCheck className="size-3.5" /> Encrypted in transit & at rest
          </div>
          <div>
            <h2 className="text-3xl font-semibold leading-tight tracking-tight">
              Care that listens, monitors, and explains.
            </h2>
            <p className="mt-3 text-white/80 max-w-md">
              Continuous vitals analysis, sourced clinical answers, and intelligent triage —
              all in one workspace built for the realities of modern medicine.
            </p>
          </div>
          <div className="flex items-center gap-6 text-sm text-white/70">
            <span>HIPAA-ready</span>
            <span className="size-1 rounded-full bg-white/40" />
            <span>SOC 2 patterns</span>
            <span className="size-1 rounded-full bg-white/40" />
            <span>JWT + RBAC</span>
          </div>
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
