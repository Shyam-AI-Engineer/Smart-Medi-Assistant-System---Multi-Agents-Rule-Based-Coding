"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessagesSquare, HeartPulse, LogOut, Settings } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vitals", label: "Vitals", icon: HeartPulse },
  { href: "/chat", label: "AI Chat", icon: MessagesSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 border-r border-border bg-bg-elevated flex-col">
      <div className="h-16 px-5 flex items-center border-b border-border">
        <Link href="/dashboard" aria-label="Home">
          <Logo />
        </Link>
      </div>

      <nav className="flex-1 p-3 space-y-0.5">
        {nav.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 h-9 px-3 rounded-md text-sm font-medium transition-colors",
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-ink-muted hover:text-ink hover:bg-bg-subtle",
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border space-y-1">
        <div className="px-3 py-2.5 rounded-md flex items-center gap-3">
          <div className="size-8 rounded-full bg-brand-100 text-brand-700 text-sm font-semibold flex items-center justify-center">
            {(user?.full_name || user?.email || "?").charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink truncate">
              {user?.full_name || "Account"}
            </p>
            <p className="text-xs text-ink-subtle truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={signOut}
          className="w-full flex items-center gap-2.5 h-9 px-3 rounded-md text-sm font-medium text-ink-muted hover:text-danger-600 hover:bg-danger-50 transition-colors"
        >
          <LogOut className="size-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}

export function MobileTopbar() {
  const pathname = usePathname();
  return (
    <div className="lg:hidden sticky top-0 z-30 h-14 border-b border-border bg-bg-elevated/90 backdrop-blur">
      <div className="h-full px-4 flex items-center justify-between">
        <Logo />
        <nav className="flex items-center gap-1">
          {nav.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                className={cn(
                  "size-9 rounded-md flex items-center justify-center transition-colors",
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-ink-muted hover:bg-bg-subtle hover:text-ink",
                )}
              >
                <Icon className="size-4" />
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
