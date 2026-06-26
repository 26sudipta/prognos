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
import { HeroCountdown } from "./countdown-display";

interface Props {
  contests: ContestItem[] | undefined;
}

export function NextContestHero({ contests }: Props) {
  if (contests === undefined) {
    return <NextContestHeroSkeleton />;
  }

  const next = getNextContest(contests);
  if (!next) return null;

  return <HeroStrip contest={next} />;
}

function HeroStrip({ contest }: { contest: ContestItem }) {
  const color = platformColor(contest.platform);
  const displayName = platformDisplayName(contest.platform);
  const startLabel = formatLocalDateTimeShort(contest.start_time);
  const endLabel = formatLocalEndLabel(contest.start_time, contest.end_time);
  const duration = formatDuration(contest.duration_seconds);

  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl overflow-hidden">
      {/* Platform-colored accent bar at top */}
      <div className="h-0.5" style={{ backgroundColor: color }} />

      <div className="flex items-center gap-6 px-6 py-5">
        {/* Countdown — fixed width so layout doesn't shift */}
        <div className="shrink-0 w-44 flex items-center justify-center">
          <HeroCountdown startTime={contest.start_time} endTime={contest.end_time} />
        </div>

        {/* Vertical divider */}
        <div className="w-px h-14 bg-border-subtle shrink-0" />

        {/* Contest info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <PlatformBadge platform={contest.platform} size="sm" />
            <span className="text-xs text-text-muted">{displayName}</span>
          </div>
          <p
            className="text-base font-semibold text-text-primary truncate"
            title={contest.name}
          >
            {contest.name}
          </p>
          <p className="text-xs text-text-muted mt-0.5">
            {startLabel} – {endLabel} · {duration}
          </p>
        </div>

        {/* Register CTA */}
        <a
          href={contest.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90"
          style={{ backgroundColor: color }}
        >
          Register
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}

export function NextContestHeroSkeleton() {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl overflow-hidden">
      <div className="skeleton h-0.5" />
      <div className="flex items-center gap-6 px-6 py-5">
        <div className="shrink-0 w-44 flex flex-col items-center gap-2">
          <div className="skeleton h-3 w-28 rounded" />
          <div className="skeleton h-10 w-36 rounded" />
        </div>
        <div className="w-px h-14 bg-border-subtle shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-3 w-20 rounded" />
          <div className="skeleton h-5 w-2/3 rounded" />
          <div className="skeleton h-3 w-48 rounded" />
        </div>
        <div className="skeleton h-10 w-28 rounded-xl shrink-0" />
      </div>
    </div>
  );
}
