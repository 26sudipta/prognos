"use client";

import { ExternalLink } from "lucide-react";
import {
  type ContestItem,
  formatLocalDateShort,
  formatLocalEndLabel,
  formatDuration,
} from "@/app/_lib/contests";
import { PlatformBadge } from "./platform-badge";
import { useCountdown } from "./countdown-display";

function pad(n: number) {
  return String(n).padStart(2, "0");
}

interface Props {
  contest: ContestItem;
  onClick?: () => void;
}

export function ContestCard({ contest, onClick }: Props) {
  const { isLive, isEnded, isSoon, isUrgent, isEndingSoon, days, hours, minutes, seconds } =
    useCountdown(contest.start_time, contest.end_time);

  // Background tint per status
  const cardBg = isEndingSoon
    ? "rgba(248,113,113,0.05)"
    : isLive
    ? "rgba(52,211,153,0.05)"
    : isSoon
    ? "rgba(34,211,238,0.04)"
    : undefined;

  // Left border per status
  const borderL = isLive
    ? "border-l-success-400"
    : isSoon
    ? "border-l-accent-400"
    : "border-l-border-subtle";

  // Name typography based on urgency priority
  const nameClass = isEnded
    ? "text-text-disabled font-normal"
    : isLive
    ? "text-text-primary font-semibold"
    : isSoon
    ? "text-text-primary font-medium"
    : "text-text-secondary font-normal";

  const startLabel = formatLocalDateShort(contest.start_time);
  const endLabel = formatLocalEndLabel(contest.start_time, contest.end_time);
  const duration = formatDuration(contest.duration_seconds);

  return (
    <div
      className={`flex items-center gap-4 border border-border-subtle border-l-[3px] ${borderL}
        rounded-xl px-4 py-3.5 hover:border-border-default transition-colors duration-150
        ${isEnded ? "opacity-40" : ""} ${onClick ? "cursor-pointer" : ""}`}
      style={cardBg ? { backgroundColor: cardBg } : undefined}
      onClick={onClick}
    >
      <PlatformBadge platform={contest.platform} />

      <div className="flex-1 min-w-0">
        <p className={`text-sm truncate ${nameClass}`} title={contest.name}>
          {contest.name}
        </p>
        <p className="text-xs text-text-muted mt-0.5">
          {startLabel} – {endLabel} · {duration}
        </p>
      </div>

      {/* Status indicator */}
      <div className="shrink-0">
        {isEnded ? (
          <span className="text-xs text-text-disabled">Ended</span>
        ) : isLive ? (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-success-400/10 border border-success-400/20 text-success-400 text-[10px] font-bold uppercase tracking-wide">
            <span className="w-1 h-1 rounded-full bg-success-400 animate-pulse shrink-0" />
            {isEndingSoon ? "Ends Soon" : "Live"}
          </span>
        ) : days >= 1 ? (
          <span className="font-mono text-xs tabular-nums text-text-muted">
            {days}d {pad(hours)}h
          </span>
        ) : (
          <span
            className={`font-mono text-xs tabular-nums ${
              isUrgent ? "text-danger-400" : isSoon ? "text-accent-400" : "text-text-muted"
            }`}
          >
            {pad(hours)}:{pad(minutes)}:{pad(seconds)}
          </span>
        )}
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
    <div className="flex items-center gap-4 border border-border-subtle border-l-[3px] border-l-border-subtle rounded-xl px-4 py-3.5">
      <div className="skeleton w-8 h-8 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-3.5 w-3/5 rounded" />
        <div className="skeleton h-3 w-2/5 rounded" />
      </div>
      <div className="skeleton h-5 w-16 rounded-full shrink-0" />
      <div className="skeleton w-4 h-4 rounded shrink-0" />
    </div>
  );
}
