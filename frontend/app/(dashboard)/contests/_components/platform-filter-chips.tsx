"use client";

import { platformColor, platformDisplayName } from "@/app/_lib/contests";

interface Props {
  platforms: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  loading: boolean;
}

export function PlatformFilterChips({ platforms, selected, onChange, loading }: Props) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 flex-nowrap overflow-x-auto sm:flex-wrap pb-1 -mb-1">
        {[72, 90, 80, 100, 88].map((w, i) => (
          <div key={i} className="skeleton h-8 rounded-full shrink-0" style={{ width: `${w}px` }} />
        ))}
      </div>
    );
  }

  const allActive = selected.length === 0;

  function togglePlatform(p: string) {
    const next = selected.includes(p)
      ? selected.filter((x) => x !== p)
      : [...selected, p];
    onChange(next);
  }

  return (
    // One horizontally-scrolling row on mobile (no tall wrapped pile), wraps on sm+.
    <div className="flex items-center gap-2 flex-nowrap overflow-x-auto sm:flex-wrap pb-1 -mb-1">
      {/* All chip */}
      <button
        onClick={() => onChange([])}
        className={`h-8 px-3.5 rounded-full text-xs font-medium whitespace-nowrap shrink-0 transition-all duration-150 border ${
          allActive
            ? "bg-primary-500/15 border-primary-500/40 text-primary-400"
            : "bg-bg-surface-raised border-border-default text-text-secondary hover:text-text-primary hover:border-border-default"
        }`}
      >
        All
      </button>

      {platforms.map((p) => {
        const color = platformColor(p);
        const name = platformDisplayName(p);
        const active = selected.includes(p);
        return (
          <button
            key={p}
            onClick={() => togglePlatform(p)}
            className={`h-8 px-3.5 rounded-full text-xs font-medium whitespace-nowrap shrink-0 transition-all duration-150 border ${
              active
                ? ""
                : "bg-bg-surface-raised border-border-default text-text-secondary hover:text-text-primary"
            }`}
            style={
              active
                ? {
                    backgroundColor: `${color}18`,
                    borderColor: `${color}50`,
                    color,
                  }
                : undefined
            }
          >
            {name}
          </button>
        );
      })}
    </div>
  );
}
