"use client";

import { useEffect, useState } from "react";
import { Share, SquarePlus, X } from "lucide-react";

const DISMISS_KEY = "prognos-ios-install-hint-dismissed";

function isIos(): boolean {
  if (/iPad|iPhone|iPod/.test(navigator.userAgent)) return true;
  // iPadOS 13+ reports itself as a Mac but is the only "Mac" with touch
  return navigator.userAgent.includes("Mac") && navigator.maxTouchPoints > 1;
}

function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    ("standalone" in navigator &&
      (navigator as { standalone?: boolean }).standalone === true)
  );
}

export function IosInstallHint() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!isIos() || isStandalone()) return;
    if (localStorage.getItem(DISMISS_KEY)) return;
    const timer = setTimeout(() => setVisible(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setVisible(false);
  };

  return (
    <div className="fixed bottom-4 inset-x-4 z-50 max-w-md mx-auto rounded-xl border border-border-default bg-bg-surface-overlay shadow-xl shadow-black/40 p-4">
      <button
        onClick={dismiss}
        aria-label="Dismiss"
        className="absolute top-2.5 right-2.5 p-1 rounded-md text-text-muted hover:text-text-primary transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
      <p className="text-sm font-semibold text-text-primary mb-2 pr-6">
        Install PROGNOS on your iPhone
      </p>
      <ol className="space-y-1.5 text-xs text-text-secondary">
        <li className="flex items-center gap-2">
          <span className="w-4 text-center font-semibold text-text-muted">1.</span>
          Tap <Share className="w-3.5 h-3.5 text-accent-400 shrink-0" /> Share in
          the Safari toolbar
        </li>
        <li className="flex items-center gap-2">
          <span className="w-4 text-center font-semibold text-text-muted">2.</span>
          Choose{" "}
          <SquarePlus className="w-3.5 h-3.5 text-accent-400 shrink-0" /> Add to
          Home Screen
        </li>
      </ol>
    </div>
  );
}
