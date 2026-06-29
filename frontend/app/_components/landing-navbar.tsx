"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { TrendingUp } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";

export default function LandingNavbar() {
  const { token, isLoading } = useAuth();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-bg-base/90 backdrop-blur-md border-b border-border-subtle"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <span className="text-sm font-bold text-text-primary tracking-tight">PROGNOS</span>
        </Link>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-7">
          <a href="#features" className="text-sm text-text-secondary hover:text-text-primary transition-colors">Features</a>
          <a href="#classrooms" className="text-sm text-text-secondary hover:text-text-primary transition-colors">Classrooms</a>
          <a href="#mobile" className="text-sm text-text-secondary hover:text-text-primary transition-colors">Mobile</a>
          <a href="#ai" className="text-sm text-text-secondary hover:text-text-primary transition-colors">AI</a>
        </nav>

        {/* Auth CTAs */}
        <div className="flex items-center gap-3">
          {!isLoading && (
            token ? (
              <Link
                href="/dashboard"
                className="px-4 py-1.5 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
              >
                Dashboard →
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="hidden sm:block text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  Log In
                </Link>
                <Link
                  href="/login"
                  className="px-4 py-1.5 rounded-lg bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )
          )}
        </div>
      </div>
    </header>
  );
}
