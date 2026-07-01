"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Lightbulb,
  Calendar,
  Link2,
  GraduationCap,
  Settings,
  TrendingUp,
  LogOut,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import { useRouter } from "next/navigation";
import { ApiError, fetchHandles, syncHandle } from "@/app/_lib/handles";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/insights",  label: "Insights",  icon: Lightbulb },
  { href: "/contests",  label: "Contests",  icon: Calendar },
  { href: "/handles",   label: "Handles",   icon: Link2 },
  { href: "/classrooms", label: "Classrooms", icon: GraduationCap },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void } = {}) {
  const pathname = usePathname();
  const { user, token, logout } = useAuth();
  const router = useRouter();
  const [syncing, setSyncing] = useState(false);
  const [syncNote, setSyncNote] = useState<string | null>(null);

  async function handleLogout() {
    onNavigate?.();
    await logout();
    router.replace("/login");
  }

  async function handleSyncNow() {
    if (!token || syncing) return;
    onNavigate?.();
    setSyncing(true);
    setSyncNote(null);
    try {
      const handles = await fetchHandles(token);
      const cf = handles.find((h) => h.platform === "codeforces" && h.is_verified);
      if (!cf) {
        setSyncNote("Verify a handle first");
        router.push("/handles");
        return;
      }
      await syncHandle(token, cf.id);
      // Give the background sync a moment to flag itself, then let the dashboard pick it
      // up (it shows the sync banner and auto-refreshes when done).
      await new Promise((r) => setTimeout(r, 1500));
      window.dispatchEvent(new Event("prognos:sync-started"));
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        const mins = Math.max(1, Math.ceil((err.retryAfterSeconds ?? 0) / 60));
        setSyncNote(`Synced recently — try again in ${mins}m`);
      } else {
        setSyncNote("Couldn't start sync — try again");
      }
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncNote(null), 5000);
    }
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
              onClick={onNavigate}
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

      {/* Bottom: sync + settings + user */}
      <div className="px-3 pb-4 border-t border-border-subtle pt-3 space-y-0.5">
        <button
          onClick={handleSyncNow}
          disabled={syncing}
          title="Fetch your latest Codeforces submissions"
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-secondary hover:bg-bg-surface-raised hover:text-text-primary transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 shrink-0 ${syncing ? "animate-spin text-primary-400" : ""}`} />
          {syncing ? "Syncing…" : "Sync now"}
        </button>
        {syncNote && (
          <p className="px-3 pb-1 text-[11px] text-text-muted leading-snug">{syncNote}</p>
        )}

        <Link
          href="/settings"
          onClick={onNavigate}
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
