"use client";

import { CohortAnalytics, cfRatingColor } from "@/app/_lib/classrooms";

interface Props {
  cohort: CohortAnalytics | undefined;
}

export function CohortAnalyticsPanel({ cohort }: Props) {
  if (!cohort) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 w-32 bg-bg-surface-raised rounded" />
        <div className="grid grid-cols-2 gap-4">
          <div className="h-36 bg-bg-surface-raised rounded-xl" />
          <div className="h-36 bg-bg-surface-raised rounded-xl" />
        </div>
        <div className="h-48 bg-bg-surface-raised rounded-xl" />
      </div>
    );
  }

  const avgRatingColor = cfRatingColor(cohort.class_average_rating ? Math.round(cohort.class_average_rating) : null);

  return (
    <div className="space-y-5">
      {/* Class average rating */}
      <div className="flex items-center gap-4 px-5 py-4 rounded-xl bg-bg-surface border border-border-subtle">
        <div>
          <p className="text-xs text-text-muted mb-0.5">Class Average Rating</p>
          <p className={`text-3xl font-bold tabular-nums ${avgRatingColor}`}>
            {cohort.class_average_rating !== null
              ? Math.round(cohort.class_average_rating)
              : "—"}
          </p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-xs text-text-muted mb-0.5">Total Students</p>
          <p className="text-2xl font-semibold text-text-primary">{cohort.member_count}</p>
        </div>
      </div>

      {/* Tag insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Most neglected */}
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle">
          <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">
            Most Neglected Tags
          </h4>
          {cohort.most_neglected_tags.length === 0 ? (
            <p className="text-xs text-text-muted">No neglected tags detected.</p>
          ) : (
            <div className="space-y-2">
              {cohort.most_neglected_tags.map((t, i) => (
                <div key={t.tag} className="flex items-center justify-between">
                  <span className="text-sm text-text-primary truncate">{t.tag}</span>
                  <span className="text-xs text-warning-400 ml-2 shrink-0">{t.count} student{t.count !== 1 ? "s" : ""}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Lowest success */}
        <div className="p-4 rounded-xl bg-bg-surface border border-border-subtle">
          <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">
            Lowest Success Tags
          </h4>
          {cohort.lowest_success_tags.length === 0 ? (
            <p className="text-xs text-text-muted">No low-success patterns detected.</p>
          ) : (
            <div className="space-y-2">
              {cohort.lowest_success_tags.map((t) => (
                <div key={t.tag} className="flex items-center justify-between">
                  <span className="text-sm text-text-primary truncate">{t.tag}</span>
                  <span className="text-xs text-danger-400 ml-2 shrink-0">{t.count} student{t.count !== 1 ? "s" : ""}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Attendance table */}
      <div className="rounded-xl bg-bg-surface border border-border-subtle overflow-hidden">
        <div className="px-4 py-3 border-b border-border-subtle">
          <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide">
            Attendance — Last 30 Days
          </h4>
        </div>
        {cohort.student_attendance.length === 0 ? (
          <p className="text-xs text-text-muted px-4 py-4">No activity data yet.</p>
        ) : (
          <div className="divide-y divide-border-subtle">
            {cohort.student_attendance.map((s) => (
              <div key={s.user_id} className="flex items-center justify-between px-4 py-2.5">
                <div className="min-w-0">
                  <span className="text-sm text-text-primary font-mono">{s.cf_handle}</span>
                  <span className="text-xs text-text-muted ml-2 truncate">{s.user_name}</span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <div
                    className="h-1.5 rounded-full bg-success-500/30"
                    style={{ width: `${Math.min(s.days_active_30d * 3.3, 100)}px` }}
                  >
                    <div
                      className="h-full rounded-full bg-success-400"
                      style={{ width: `${Math.min((s.days_active_30d / 30) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-text-muted w-10 text-right tabular-nums">
                    {s.days_active_30d}/30
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
