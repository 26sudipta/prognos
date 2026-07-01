"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Menu, TrendingUp } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import { Sidebar } from "@/app/_components/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { token, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/login");
    }
  }, [token, isLoading, router]);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-base flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!token) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      {/* Desktop sidebar */}
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {/* Mobile drawer: backdrop + off-canvas sidebar */}
      <div
        aria-hidden={!drawerOpen}
        onClick={() => setDrawerOpen(false)}
        className={`fixed inset-0 z-40 bg-black/50 md:hidden transition-opacity duration-200 ${
          drawerOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      />
      <div
        className={`fixed inset-y-0 left-0 z-50 md:hidden transition-transform duration-200 ease-out ${
          drawerOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar onNavigate={() => setDrawerOpen(false)} />
      </div>

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Mobile top bar */}
        <header className="md:hidden flex items-center gap-3 h-14 px-4 border-b border-border-subtle bg-bg-surface shrink-0">
          <button
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
            className="p-1.5 -ml-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-surface-raised transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-primary-500 flex items-center justify-center">
              <TrendingUp className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
            </div>
            <span className="font-bold text-text-primary text-sm tracking-tight">PROGNOS</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6 min-w-0">{children}</main>
      </div>
    </div>
  );
}
