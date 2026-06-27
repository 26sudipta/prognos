"use client";

import { useState, useEffect } from "react";

// ─── Hook ─────────────────────────────────────────────────────────────────────

export interface CountdownState {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  totalSeconds: number;
  isLive: boolean;        // started, not yet ended
  isEnded: boolean;       // past end_time
  isSoon: boolean;        // < 24h until start
  isUrgent: boolean;      // < 1h until start
  isEndingSoon: boolean;  // live and < 1h remaining
}

export function useCountdown(startTime: string, endTime: string): CountdownState {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();
  const isLive = now >= start && now < end;
  const isEnded = now >= end;

  // Remaining time: to start if upcoming, to end if live
  const targetMs = isEnded ? 0 : isLive ? end - now : start - now;
  const totalSeconds = Math.max(0, Math.floor(targetMs / 1000));

  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const isSoon = !isLive && !isEnded && totalSeconds < 86400;
  const isUrgent = !isLive && !isEnded && totalSeconds < 3600;
  const isEndingSoon = isLive && totalSeconds < 3600;

  return { days, hours, minutes, seconds, totalSeconds, isLive, isEnded, isSoon, isUrgent, isEndingSoon };
}

// ─── Display component (card-sized) ──────────────────────────────────────────

function pad(n: number) {
  return String(n).padStart(2, "0");
}

interface Props {
  startTime: string;
  endTime: string;
  className?: string;
}

export function CountdownDisplay({ startTime, endTime, className = "" }: Props) {
  const { days, hours, minutes, seconds, isLive, isEnded, isSoon, isUrgent } =
    useCountdown(startTime, endTime);

  if (isEnded) {
    return <span className={`text-text-muted text-xs ${className}`}>Ended</span>;
  }

  if (isLive) {
    return (
      <span className={`flex items-center gap-1.5 ${className}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-success-400 animate-pulse shrink-0" />
        <span className="text-success-400 text-xs font-semibold tracking-wide">LIVE</span>
        <span className="text-danger-400 font-mono text-xs tabular-nums">
          ends {pad(hours)}:{pad(minutes)}:{pad(seconds)}
        </span>
      </span>
    );
  }

  const colorClass = isUrgent
    ? "text-danger-400"
    : isSoon
    ? "text-accent-400"
    : "text-text-muted";

  // >1 day: "3d 14h"
  if (days >= 1) {
    return (
      <span className={`font-mono text-xs tabular-nums ${colorClass} ${className}`}>
        {days}d {pad(hours)}h
      </span>
    );
  }

  // <24h: "HH:MM:SS"
  return (
    <span className={`font-mono text-xs tabular-nums ${colorClass} ${className}`}>
      {pad(hours)}:{pad(minutes)}:{pad(seconds)}
    </span>
  );
}

// ─── Hero-sized countdown (large, segmented) ──────────────────────────────────

function HeroSegment({
  value,
  label,
  colorClass,
}: {
  value: number;
  label: string;
  colorClass: string;
}) {
  return (
    <div className="flex flex-col items-center">
      <span className={`text-4xl leading-none font-mono font-bold tabular-nums ${colorClass}`}>
        {pad(value)}
      </span>
      <span className="text-[9px] text-text-muted uppercase tracking-widest mt-1">{label}</span>
    </div>
  );
}

function HeroSep({ colorClass }: { colorClass: string }) {
  return (
    <span
      className={`text-4xl leading-none font-mono font-bold mb-[12px] ${colorClass} select-none`}
    >
      :
    </span>
  );
}

export function HeroCountdown({ startTime, endTime }: { startTime: string; endTime: string }) {
  const { days, hours, minutes, seconds, isLive, isEnded, isSoon, isUrgent } =
    useCountdown(startTime, endTime);

  if (isEnded) return null;

  if (isLive) {
    return (
      <div className="flex flex-col items-center">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="w-2 h-2 rounded-full bg-success-400 animate-pulse" />
          <span className="text-success-400 text-sm font-bold tracking-wider uppercase">
            Live Now
          </span>
        </div>
        <span className="font-mono text-3xl tabular-nums text-danger-400 font-bold">
          {pad(hours)}:{pad(minutes)}:{pad(seconds)}
        </span>
        <span className="text-[10px] text-text-muted mt-1 uppercase tracking-widest">
          remaining
        </span>
      </div>
    );
  }

  const colorClass = isUrgent
    ? "text-danger-400"
    : isSoon
    ? "text-accent-400"
    : "text-text-primary";

  return (
    <div className="flex flex-col items-center">
      <span className="text-[10px] text-text-muted uppercase tracking-widest mb-3">
        Next contest in
      </span>
      <div className="flex items-end gap-1">
        {days >= 1 ? (
          <>
            <HeroSegment value={days} label="d" colorClass={colorClass} />
            <HeroSep colorClass={colorClass} />
            <HeroSegment value={hours} label="h" colorClass={colorClass} />
            <HeroSep colorClass={colorClass} />
            <HeroSegment value={minutes} label="m" colorClass={colorClass} />
          </>
        ) : (
          <>
            <HeroSegment value={hours} label="h" colorClass={colorClass} />
            <HeroSep colorClass={colorClass} />
            <HeroSegment value={minutes} label="m" colorClass={colorClass} />
            <HeroSep colorClass={colorClass} />
            <HeroSegment value={seconds} label="s" colorClass={colorClass} />
          </>
        )}
      </div>
    </div>
  );
}
