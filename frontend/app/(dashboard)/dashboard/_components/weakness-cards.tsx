"use client";

import type { WeaknessSignal, WeaknessSignalType } from "@/app/_lib/analytics";

const SIGNAL_CFG: Record<
  WeaknessSignalType,
  { label: string; color: string; bg: string; border: string }
> = {
  low_success: {
    label: "Low Success",
    color: "#F87171",
    bg: "rgba(248,113,113,0.06)",
    border: "rgba(248,113,113,0.25)",
  },
  neglected: {
    label: "Neglected",
    color: "#FBBF24",
    bg: "rgba(251,191,36,0.06)",
    border: "rgba(251,191,36,0.25)",
  },
  under_practiced: {
    label: "Under-practiced",
    color: "#22D3EE",
    bg: "rgba(34,211,238,0.06)",
    border: "rgba(34,211,238,0.25)",
  },
};

// Visual urgency: score ranges roughly 0–3; clamp to 5 filled dots
function urgencyDots(score: number): number {
  return Math.min(5, Math.max(1, Math.round((score / 3) * 5)));
}

interface Props {
  data: WeaknessSignal[];
}

export function WeaknessCards({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full flex items-center justify-center min-h-[200px]">
        <p className="text-sm text-text-muted">No weaknesses detected yet.</p>
      </div>
    );
  }

  // All signals in a batch share the same computed_at
  const analyzedAt = data[0].computed_at;
  const analyzedLabel = new Date(analyzedAt).toLocaleDateString("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 h-full">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">
          Weaknesses
        </h2>
        <span className="text-[10px] text-text-disabled">analyzed {analyzedLabel}</span>
      </div>

      <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
        {data.map((s) => {
          const cfg = SIGNAL_CFG[s.signal_type];
          const dots = urgencyDots(s.score);
          return (
            <div
              key={s.id}
              className="rounded-lg border p-3.5"
              style={{ backgroundColor: cfg.bg, borderColor: cfg.border }}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="text-sm font-medium text-text-primary truncate">{s.tag}</span>
                <span
                  className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full border whitespace-nowrap"
                  style={{ color: cfg.color, borderColor: cfg.border, backgroundColor: cfg.bg }}
                >
                  {cfg.label}
                </span>
              </div>

              <p className="text-xs text-text-muted leading-relaxed">{s.reason}</p>

              {/* Urgency dots */}
              <div className="flex items-center gap-1 mt-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      backgroundColor: i <= dots ? cfg.color : "rgba(255,255,255,0.08)",
                    }}
                  />
                ))}
                <span className="text-[10px] text-text-disabled ml-1.5">urgency</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function WeaknessCardsSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex justify-between mb-4">
        <div className="skeleton h-3 w-24" />
        <div className="skeleton h-3 w-20" />
      </div>
      <div className="space-y-2.5">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton h-[90px] w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}
