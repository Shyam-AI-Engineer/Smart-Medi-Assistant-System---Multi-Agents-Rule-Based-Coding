"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, LogOut, ShieldCheck, ClipboardList, Users } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";

const nav = [
  { href: "/admin/dashboard", label: "Analytics", icon: LayoutDashboard },
  { href: "/admin/audit-logs", label: "Audit Logs", icon: ClipboardList },
  { href: "/admin/users", label: "Users", icon: Users },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <aside className="hidden lg:flex w-64 shrink-0 border-r border-border bg-bg-elevated flex-col">
      <div className="h-16 px-5 flex items-center gap-2.5 border-b border-border">
        <Link href="/admin/dashboard" aria-label="Home">
          <Logo />
        </Link>
        <span className="text-xs font-semibold text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">
          Admin
        </span>
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
              <Icon className="size-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border space-y-1">
        <div className="px-3 py-2.5 rounded-md flex items-center gap-3">
          <div className="size-8 rounded-full bg-brand-100 text-brand-700 text-sm font-semibold flex items-center justify-center">
            <ShieldCheck className="size-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink truncate">
              {user?.full_name || "Admin"}
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

export function AdminMobileTopbar() {
  const { signOut } = useAuth();
  return (
    <div className="lg:hidden sticky top-0 z-30 h-14 border-b border-border bg-bg-elevated/90 backdrop-blur">
      <div className="h-full px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Logo />
          <span className="text-xs font-semibold text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">
            Admin
          </span>
        </div>
        <button
          onClick={signOut}
          className="text-xs text-ink-muted hover:text-danger-600 transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
