"use client";

import { useState } from "react";
import { UserMinus, Loader2 } from "lucide-react";
import { Member, removeMember } from "@/app/_lib/classrooms";

interface Props {
  classroomId: string;
  token: string;
  ownerId: string;
  members: Member[];
  onMembersChange: (members: Member[]) => void;
}

export function MemberManagement({ classroomId, token, ownerId, members, onMembersChange }: Props) {
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  async function handleRemove(userId: string) {
    setRemovingId(userId);
    try {
      await removeMember(token, classroomId, userId);
      onMembersChange(members.filter((m) => m.user_id !== userId));
    } catch {
      // keep member in list on error
    } finally {
      setRemovingId(null);
      setConfirmId(null);
    }
  }

  return (
    <div className="space-y-3">
      {members.map((m) => (
        <div
          key={m.user_id}
          className="flex items-center justify-between px-4 py-3 rounded-xl bg-bg-surface border border-border-subtle"
        >
          <div className="flex items-center gap-3 min-w-0">
            {/* Avatar placeholder */}
            <div className="w-8 h-8 rounded-full bg-primary-600/20 flex items-center justify-center shrink-0 text-sm font-semibold text-primary-400">
              {m.user_name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary truncate">{m.user_name}</span>
                <span
                  className={`text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide ${
                    m.role === "teacher"
                      ? "bg-primary-500/10 text-primary-400"
                      : "bg-bg-surface-raised text-text-muted"
                  }`}
                >
                  {m.role}
                </span>
              </div>
              {m.cf_handle && (
                <span className="text-xs text-text-muted font-mono">{m.cf_handle}</span>
              )}
            </div>
          </div>

          {/* Remove button — only for students */}
          {m.role === "student" && (
            confirmId === m.user_id ? (
              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => handleRemove(m.user_id)}
                  disabled={removingId === m.user_id}
                  className="text-[11px] px-2 py-1 rounded bg-danger-500/10 text-danger-400 hover:bg-danger-500/20 transition-colors"
                >
                  {removingId === m.user_id ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    "Confirm"
                  )}
                </button>
                <button
                  onClick={() => setConfirmId(null)}
                  className="text-[11px] px-2 py-1 rounded bg-bg-surface-raised text-text-muted hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmId(m.user_id)}
                className="shrink-0 p-1.5 rounded text-text-muted hover:text-danger-400 transition-colors"
                title="Remove student"
              >
                <UserMinus className="w-4 h-4" />
              </button>
            )
          )}
        </div>
      ))}
    </div>
  );
}
