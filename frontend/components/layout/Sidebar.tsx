"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessagesSquare, HeartPulse, FileText, Pill, LogOut, Settings, Stethoscope, Inbox } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { useAuth } from "@/hooks/useAuth";
import { useMessages } from "@/hooks/useMessages";
import { cn } from "@/lib/cn";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vitals", label: "Vitals", icon: HeartPulse },
  { href: "/medications", label: "Medications", icon: Pill },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/triage", label: "Symptom Checker", icon: Stethoscope },
  { href: "/chat", label: "AI Chat", icon: MessagesSquare },
  { href: "/messages", label: "Messages", icon: Inbox },
  { href: "/profile", label: "Profile", icon: Settings },
];

function UnreadBadge({ count }: { count: number }) {
  if (count === 0) return null;
  return (
    <span className="ml-auto min-w-[18px] h-[18px] px-1 rounded-full bg-brand-500 text-white text-[10px] font-bold flex items-center justify-center">
      {count > 9 ? "9+" : count}
    </span>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const { data: messagesData } = useMessages();
  const unreadCount = messagesData?.unread_count ?? 0;

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
          const isMessages = item.href === "/messages";
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
              {isMessages && <UnreadBadge count={unreadCount} />}
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
