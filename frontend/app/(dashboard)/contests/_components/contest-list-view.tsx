"use client";

import { Calendar } from "lucide-react";
import {
  type ContestItem,
  groupContestsByLocalDate,
  formatDateHeader,
} from "@/app/_lib/contests";
import { ContestCard, ContestCardSkeleton } from "./contest-card";

interface Props {
  contests: ContestItem[] | undefined;
  selectedPlatforms: string[];
  onClearFilter: () => void;
  onContestClick: (c: ContestItem) => void;
}

export function ContestListView({
  contests,
  selectedPlatforms,
  onClearFilter,
  onContestClick,
}: Props) {
  if (contests === undefined) {
    return <ContestListSkeleton />;
  }

  if (contests.length === 0) {
    return (
      <EmptyState
        selectedPlatforms={selectedPlatforms}
        onClearFilter={onClearFilter}
      />
    );
  }

  const groups = groupContestsByLocalDate(contests);

  return (
    <div className="space-y-6">
      {groups.map(({ date, contests: groupContests }) => (
        <div key={date}>
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-3 flex items-center gap-3">
            {formatDateHeader(date)}
            <span className="flex-1 h-px bg-border-subtle" />
          </h3>
          <div className="space-y-2">
            {groupContests.map((c) => (
              <ContestCard
                key={c.id}
                contest={c}
                onClick={() => onContestClick(c)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({
  selectedPlatforms,
  onClearFilter,
}: {
  selectedPlatforms: string[];
  onClearFilter: () => void;
}) {
  const filterLabel =
    selectedPlatforms.length === 1
      ? selectedPlatforms[0]
      : selectedPlatforms.length > 1
      ? `${selectedPlatforms.length} platforms`
      : null;

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-bg-surface-raised border border-border-default mb-4">
        <Calendar className="w-5 h-5 text-text-muted" />
      </div>
      <p className="text-sm font-medium text-text-secondary mb-1">
        {filterLabel
          ? `No ${filterLabel} contests in the next 30 days.`
          : "No upcoming contests in the next 30 days."}
      </p>
      {filterLabel && (
        <button
          onClick={onClearFilter}
          className="text-xs text-primary-400 hover:text-primary-300 transition-colors mt-1"
        >
          Clear filter
        </button>
      )}
    </div>
  );
}

export function ContestListSkeleton() {
  return (
    <div className="space-y-6">
      {[0, 1, 2].map((g) => (
        <div key={g}>
          <div className="flex items-center gap-3 mb-3">
            <div className="skeleton h-3 w-36 rounded" />
            <div className="flex-1 h-px bg-border-subtle" />
          </div>
          <div className="space-y-2">
            {[0, 1].map((i) => (
              <ContestCardSkeleton key={i} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
