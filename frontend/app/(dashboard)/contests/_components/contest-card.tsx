"use client";

import { ExternalLink } from "lucide-react";
import {
  type ContestItem,
  formatLocalDateTimeShort,
  formatLocalEndLabel,
  formatDuration,
} from "@/app/_lib/contests";
import { PlatformBadge } from "./platform-badge";
import { CountdownDisplay, useCountdown } from "./countdown-display";

interface Props {
  contest: ContestItem;
  onClick?: () => void;
}

export function ContestCard({ contest, onClick }: Props) {
  const { isLive, isEnded, isSoon } = useCountdown(contest.start_time, contest.end_time);

  const borderColor = isLive
    ? "border-l-success-400"
    : isSoon
    ? "border-l-accent-400"
    : "border-l-border-subtle";

  const startLabel = formatLocalDateTimeShort(contest.start_time);
  const endLabel = formatLocalEndLabel(contest.start_time, contest.end_time);
  const duration = formatDuration(contest.duration_seconds);

  return (
    <div
      className={`flex items-center gap-4 bg-bg-surface border border-border-subtle border-l-[3px]
        ${borderColor} rounded-xl px-4 py-3.5 hover:border-border-default transition-colors duration-150
        ${isEnded ? "opacity-50" : ""} ${onClick ? "cursor-pointer" : ""}`}
      onClick={onClick}
    >
      <PlatformBadge platform={contest.platform} />

      <div className="flex-1 min-w-0">
        <p
          className="text-sm font-medium text-text-primary truncate"
          title={contest.name}
        >
          {contest.name}
        </p>
        <p className="text-xs text-text-muted mt-0.5">
          {startLabel} – {endLabel} · {duration}
        </p>
      </div>

      <div className="shrink-0">
        <CountdownDisplay startTime={contest.start_time} endTime={contest.end_time} />
      </div>

      <a
        href={contest.url}
        target="_blank"
        rel="noopener noreferrer"
        className="shrink-0 text-text-muted hover:text-text-primary transition-colors duration-150 ml-1"
        title={isLive ? "Open contest" : "Register"}
        onClick={(e) => e.stopPropagation()}
      >
        <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
}

export function ContestCardSkeleton() {
  return (
    <div className="flex items-center gap-4 bg-bg-surface border border-border-subtle border-l-[3px] border-l-border-subtle rounded-xl px-4 py-3.5">
      <div className="skeleton w-8 h-8 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-3.5 w-3/5 rounded" />
        <div className="skeleton h-3 w-2/5 rounded" />
      </div>
      <div className="skeleton h-3 w-14 rounded shrink-0" />
      <div className="skeleton w-4 h-4 rounded shrink-0" />
    </div>
  );
}
