"use client";

import { useEffect } from "react";
import { X, ExternalLink, Clock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import {
  type ContestItem,
  formatLocalDateTimeLong,
  formatLocalEndLabel,
  formatDuration,
  platformDisplayName,
} from "@/app/_lib/contests";
import { PlatformBadge } from "./platform-badge";
import { CountdownDisplay } from "./countdown-display";

interface Props {
  contest: ContestItem | null;
  onClose: () => void;
}

export function ContestDetailModal({ contest, onClose }: Props) {
  // Close on Escape — only register while the modal is open
  useEffect(() => {
    if (!contest) return;
    function handler(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [contest, onClose]);

  return (
    <AnimatePresence>
      {contest && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/60 z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            key="panel"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div
              className="bg-bg-surface-raised border border-border-default rounded-2xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <ModalContent contest={contest} onClose={onClose} />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function ModalContent({ contest, onClose }: { contest: ContestItem; onClose: () => void }) {
  const startLong = formatLocalDateTimeLong(contest.start_time);
  const endTime = formatLocalEndLabel(contest.start_time, contest.end_time);
  const duration = formatDuration(contest.duration_seconds);
  const platform = platformDisplayName(contest.platform);

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-5">
        <div className="flex items-center gap-3 min-w-0">
          <PlatformBadge platform={contest.platform} />
          <div className="min-w-0">
            <p className="text-xs text-text-muted mb-0.5">{platform}</p>
            <h2
              className="text-base font-semibold text-text-primary leading-snug"
              title={contest.name}
            >
              {contest.name}
            </h2>
          </div>
        </div>
        <button
          onClick={onClose}
          className="shrink-0 text-text-muted hover:text-text-primary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Divider */}
      <div className="h-px bg-border-subtle mb-5" />

      {/* Info rows */}
      <dl className="space-y-3 text-sm mb-5">
        <Row label="Starts">
          {startLong}
        </Row>
        <Row label="Ends">
          {endTime}
        </Row>
        <Row label="Duration">
          <span className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-text-muted" />
            {duration}
          </span>
        </Row>
        <Row label="Status">
          <CountdownDisplay
            startTime={contest.start_time}
            endTime={contest.end_time}
          />
        </Row>
      </dl>

      {/* CTA */}
      <a
        href={contest.url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-semibold transition-colors"
      >
        Open on {platform}
        <ExternalLink className="w-4 h-4" />
      </a>
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <dt className="text-text-muted w-20 shrink-0 pt-px">{label}</dt>
      <dd className="text-text-primary">{children}</dd>
    </div>
  );
}
