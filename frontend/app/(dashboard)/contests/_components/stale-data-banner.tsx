"use client";

import { AlertTriangle } from "lucide-react";

interface Props {
  isStale: boolean;
}

export function StaleDataBanner({ isStale }: Props) {
  if (!isStale) return null;

  return (
    <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-warning-500/10 border border-warning-500/30 text-warning-400 text-xs">
      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
      <span>Contest data may be outdated. Last sync was more than 8 hours ago.</span>
    </div>
  );
}
