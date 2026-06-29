"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Link2,
  GraduationCap,
  Settings,
  TrendingUp,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import { useRouter } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/contests",  label: "Contests",  icon: Calendar },
  { href: "/handles",   label: "Handles",   icon: Link2 },
  { href: "/classrooms", label: "Classrooms", icon: GraduationCap },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <aside className="flex flex-col w-60 shrink-0 h-screen bg-bg-surface border-r border-border-subtle sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-border-subtle">
        <div className="w-7 h-7 rounded-lg bg-primary-500 flex items-center justify-center shrink-0">
          <TrendingUp className="w-4 h-4 text-white" strokeWidth={2.5} />
        </div>
        <span className="font-bold text-text-primary tracking-tight">PROGNOS</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 ${
                active
                  ? "bg-primary-500/10 text-primary-400"
                  : "text-text-secondary hover:bg-bg-surface-raised hover:text-text-primary"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom: settings + user */}
      <div className="px-3 pb-4 border-t border-border-subtle pt-3 space-y-0.5">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-bg-surface-raised hover:text-text-primary transition-colors duration-150"
        >
          <Settings className="w-4 h-4 shrink-0" />
          Settings
        </Link>

        {/* User row */}
        {user && (
          <div className="flex items-center gap-2.5 px-3 py-2 mt-1">
            {user.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.name}
                className="w-7 h-7 rounded-full shrink-0 object-cover"
              />
            ) : (
              <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center text-xs font-semibold text-white shrink-0">
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">{user.name}</p>
              <p className="text-xs text-text-muted truncate">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="shrink-0 text-text-muted hover:text-danger-400 transition-colors duration-150"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
