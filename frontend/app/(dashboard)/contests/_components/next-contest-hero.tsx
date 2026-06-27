"use client";

import { ExternalLink } from "lucide-react";
import {
  type ContestItem,
  formatLocalDateTimeShort,
  formatLocalEndLabel,
  formatDuration,
  platformColor,
  platformDisplayName,
  getNextContest,
} from "@/app/_lib/contests";
import { PlatformBadge } from "./platform-badge";
import { useCountdown } from "./countdown-display";

// ─── Arc constants ────────────────────────────────────────────────────────────

const RADIUS = 60;
const CIRC = 2 * Math.PI * RADIUS; // ≈ 376.99
const CX = 80;
const CY = 80;

function pad(n: number) {
  return String(n).padStart(2, "0");
}

// ─── Public component ─────────────────────────────────────────────────────────

interface Props {
  contests: ContestItem[] | undefined;
}

export function NextContestHero({ contests }: Props) {
  if (contests === undefined) return <NextContestHeroSkeleton />;
  const next = getNextContest(contests);
  if (!next) return null;
  return <HeroStrip contest={next} />;
}

// ─── Hero strip ───────────────────────────────────────────────────────────────

function HeroStrip({ contest }: { contest: ContestItem }) {
  const color = platformColor(contest.platform);
  const { isLive, isEnded, isSoon, isUrgent, isEndingSoon, days, hours, minutes, seconds, totalSeconds } =
    useCountdown(contest.start_time, contest.end_time);

  if (isEnded) return null;

  // Semantic arc color
  const arcColor = isEndingSoon
    ? "#F87171"   // danger-400
    : isLive
    ? "#34D399"   // success-400
    : isSoon || isUrgent
    ? "#22D3EE"   // accent-400
    : "#818CF8";  // primary-400

  // Arc fill: 0→1 during live contest; 0→1 in the final 24h before start; 0 otherwise
  const arcProgress = isLive && contest.duration_seconds > 0
    ? Math.min(1, Math.max(0, 1 - totalSeconds / contest.duration_seconds))
    : !isLive && totalSeconds < 86400
    ? (86400 - totalSeconds) / 86400
    : 0;

  // Hero gradient tint based on status
  const heroTint = isEndingSoon
    ? "rgba(248,113,113,0.07)"
    : isLive
    ? "rgba(52,211,153,0.07)"
    : `${color}0D`; // ~5% platform tint when upcoming

  const startLabel = formatLocalDateTimeShort(contest.start_time);
  const endLabel = formatLocalEndLabel(contest.start_time, contest.end_time);
  const duration = formatDuration(contest.duration_seconds);
  const displayName = platformDisplayName(contest.platform);

  return (
    <div
      className="border border-border-default rounded-2xl overflow-hidden"
      style={{
        background: `linear-gradient(135deg, ${heroTint} 0%, transparent 60%), var(--bg-surface)`,
      }}
    >
      {/* Platform-colored top bar */}
      <div className="h-[2px]" style={{ backgroundColor: color }} />

      {/* Body: arc panel + divider + info panel */}
      <div className="flex items-stretch">
        {/* Arc countdown panel */}
        <div className="w-64 shrink-0 flex items-center justify-center py-8 px-6">
          <ArcCountdownPanel
            days={days}
            hours={hours}
            minutes={minutes}
            seconds={seconds}
            isLive={isLive}
            isEndingSoon={isEndingSoon}
            isSoon={isSoon}
            arcColor={arcColor}
            arcProgress={arcProgress}
          />
        </div>

        {/* Vertical divider */}
        <div
          className="w-px shrink-0 my-6"
          style={{ backgroundColor: "var(--border-subtle)" }}
        />

        {/* Info panel */}
        <div className="flex-1 min-w-0 flex flex-col justify-center gap-5 px-8 py-8">
          {/* Status label */}
          <div>
            {isLive ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success-400/10 border border-success-400/20 text-success-400 text-[10px] font-bold uppercase tracking-widest">
                <span className="w-1.5 h-1.5 rounded-full bg-success-400 animate-pulse shrink-0" />
                Live Now
              </span>
            ) : (
              <span className="text-[10px] text-text-muted uppercase tracking-widest font-medium">
                Up Next
              </span>
            )}
          </div>

          {/* Contest identity */}
          <div className="space-y-1.5 min-w-0">
            <h2
              className="text-2xl font-bold text-text-primary leading-tight"
              title={contest.name}
            >
              {contest.name}
            </h2>
            <div className="flex items-center gap-2">
              <PlatformBadge platform={contest.platform} size="sm" />
              <span className="text-xs text-text-muted">{displayName}</span>
            </div>
            <p className="text-xs text-text-muted">
              {startLabel} – {endLabel} · {duration}
            </p>
          </div>

          {/* CTA */}
          <a
            href={contest.url}
            target="_blank"
            rel="noopener noreferrer"
            className="self-start flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-85"
            style={{ backgroundColor: color }}
          >
            {isLive ? "Open Contest" : "Register"}
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}

// ─── Arc countdown panel ──────────────────────────────────────────────────────

interface ArcCountdownPanelProps {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isLive: boolean;
  isEndingSoon: boolean;
  isSoon: boolean;
  arcColor: string;
  arcProgress: number;
}

function ArcCountdownPanel({
  days,
  hours,
  minutes,
  seconds,
  isLive,
  isEndingSoon,
  isSoon,
  arcColor,
  arcProgress,
}: ArcCountdownPanelProps) {
  const dashOffset = CIRC * (1 - arcProgress);

  // Countdown text color matches arc except for default upcoming (keep primary readable)
  const countdownColor = isEndingSoon
    ? "#F87171"
    : isLive
    ? "#34D399"
    : isSoon
    ? "#22D3EE"
    : "#F1F5F9"; // text-primary for far-future

  return (
    <div className="relative w-[160px] h-[160px]">
      {/* SVG arc ring */}
      <svg
        width="160"
        height="160"
        viewBox="0 0 160 160"
        className="absolute inset-0"
        aria-hidden="true"
      >
        {/* Track */}
        <circle
          cx={CX}
          cy={CY}
          r={RADIUS}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={5}
        />
        {/* Progress arc (invisible when dashOffset = CIRC) */}
        <circle
          cx={CX}
          cy={CY}
          r={RADIUS}
          fill="none"
          stroke={arcColor}
          strokeWidth={5}
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${CX} ${CY})`}
          style={{ transition: "stroke-dashoffset 0.8s linear" }}
        />
      </svg>

      {/* Countdown content centered in ring */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5 px-4">
        {isLive ? (
          <>
            <span className="flex items-center gap-1 mb-1">
              <span className="w-1 h-1 rounded-full bg-success-400 animate-pulse shrink-0" />
              <span className="text-[9px] text-success-400 uppercase tracking-widest font-bold">
                Live
              </span>
            </span>
            <span
              className="font-mono text-xl tabular-nums font-bold leading-none"
              style={{ color: countdownColor }}
            >
              {pad(hours)}:{pad(minutes)}:{pad(seconds)}
            </span>
            <span className="text-[9px] text-text-muted uppercase tracking-widest mt-1">
              remaining
            </span>
          </>
        ) : days >= 1 ? (
          <>
            <span
              className="font-mono text-3xl tabular-nums font-bold leading-none"
              style={{ color: countdownColor }}
            >
              {days}d
            </span>
            <span className="font-mono text-base tabular-nums font-semibold text-text-secondary leading-none mt-1">
              {pad(hours)}h {pad(minutes)}m
            </span>
            <span className="text-[9px] text-text-muted uppercase tracking-widest mt-2">
              until start
            </span>
          </>
        ) : (
          <>
            <span
              className="font-mono text-xl tabular-nums font-bold leading-none"
              style={{ color: countdownColor }}
            >
              {pad(hours)}:{pad(minutes)}:{pad(seconds)}
            </span>
            <span className="text-[9px] text-text-muted uppercase tracking-widest mt-1">
              until start
            </span>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Skeleton ──────────────────────────────────────────────────────────────────

export function NextContestHeroSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-default rounded-2xl overflow-hidden">
      <div className="h-[2px] skeleton" />
      <div className="flex items-stretch">
        <div className="w-64 shrink-0 flex items-center justify-center py-8 px-6">
          <div className="relative w-[160px] h-[160px]">
            <svg width="160" height="160" viewBox="0 0 160 160" aria-hidden="true">
              <circle
                cx={CX} cy={CY} r={RADIUS}
                fill="none"
                stroke="rgba(255,255,255,0.06)"
                strokeWidth={5}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <div className="skeleton h-8 w-16 rounded" />
              <div className="skeleton h-4 w-20 rounded" />
              <div className="skeleton h-2.5 w-14 rounded mt-1" />
            </div>
          </div>
        </div>
        <div className="w-px shrink-0 my-6" style={{ backgroundColor: "var(--border-subtle)" }} />
        <div className="flex-1 flex flex-col justify-center gap-5 px-8 py-8">
          <div className="skeleton h-3 w-16 rounded" />
          <div className="space-y-2">
            <div className="skeleton h-8 w-3/4 rounded" />
            <div className="skeleton h-4 w-28 rounded" />
            <div className="skeleton h-3 w-52 rounded" />
          </div>
          <div className="skeleton h-10 w-32 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
