"use client";

import { platformAbbr, platformColor } from "@/app/_lib/contests";

interface Props {
  platform: string;
  size?: "sm" | "md";
}

export function PlatformBadge({ platform, size = "md" }: Props) {
  const color = platformColor(platform);
  const abbr = platformAbbr(platform);
  const sizeClass = size === "sm" ? "w-6 h-6 text-[9px]" : "w-8 h-8 text-[11px]";

  return (
    <div
      className={`${sizeClass} rounded-lg flex items-center justify-center font-mono font-bold shrink-0`}
      style={{ backgroundColor: `${color}22`, color }}
    >
      {abbr}
    </div>
  );
}
