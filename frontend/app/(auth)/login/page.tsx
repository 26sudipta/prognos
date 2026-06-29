import Link from "next/link";
import { TrendingUp, ArrowLeft } from "lucide-react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-bg-base flex items-center justify-center px-4">
      {/* Background gradient blob */}
      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden
      >
        <div
          className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full opacity-10"
          style={{
            background:
              "radial-gradient(circle, #6366F1 0%, #06B6D4 50%, transparent 70%)",
            filter: "blur(80px)",
          }}
        />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Back to home */}
        <Link
          href="/"
          className="absolute -top-10 left-0 flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to home
        </Link>
        {/* Logo */}
        <div className="flex flex-col items-center gap-3 mb-10">
          <div className="w-12 h-12 rounded-xl bg-primary-500 flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" strokeWidth={2.5} />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">
              PROGNOS
            </h1>
            <p className="text-sm text-text-muted mt-1">
              Track. Analyze. Improve.
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-bg-surface border border-border-subtle rounded-xl p-8">
          <h2 className="text-lg font-semibold text-text-primary mb-1">
            Welcome back
          </h2>
          <p className="text-sm text-text-secondary mb-6">
            Sign in to access your competitive programming dashboard.
          </p>

          <a
            href={`${API_URL}/api/v1/auth/google`}
            className="flex items-center justify-center gap-3 w-full py-2.5 px-4 rounded-lg border border-border-default bg-bg-surface-raised text-text-primary text-sm font-medium hover:bg-bg-surface-overlay hover:border-border-default transition-colors duration-150"
          >
            {/* Google SVG logo */}
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
              <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
              <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
              <path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
              <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </a>

          <p className="text-xs text-text-muted text-center mt-5">
            By signing in, you agree to our terms of service.
          </p>
        </div>
      </div>
    </main>
  );
}
