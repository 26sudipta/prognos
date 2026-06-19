"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/app/_components/auth-provider";
import { Loader2 } from "lucide-react";

function CallbackHandler() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      login(token);
      window.history.replaceState({}, "", "/auth/callback");
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [login, params, router]);

  return (
    <div className="flex flex-col items-center gap-3 text-text-secondary">
      <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      <p className="text-sm">Signing you in…</p>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <main className="min-h-screen bg-bg-base flex items-center justify-center">
      <Suspense
        fallback={
          <div className="flex flex-col items-center gap-3 text-text-secondary">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            <p className="text-sm">Signing you in…</p>
          </div>
        }
      >
        <CallbackHandler />
      </Suspense>
    </main>
  );
}
