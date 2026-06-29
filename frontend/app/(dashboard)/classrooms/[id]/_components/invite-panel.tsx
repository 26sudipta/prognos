"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Link, Plus, Copy, Check, Trash2, Loader2 } from "lucide-react";
import { Invite, createInvite, revokeInvite, fetchInvites, formatExpiresAt } from "@/app/_lib/classrooms";

interface Props {
  classroomId: string;
  token: string;
  invites: Invite[];
  onInvitesChange: (invites: Invite[]) => void;
}

export function InvitePanel({ classroomId, token, invites, onInvitesChange }: Props) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [confirmRevokeId, setConfirmRevokeId] = useState<string | null>(null);

  async function handleGenerate() {
    setIsGenerating(true);
    try {
      const inv = await createInvite(token, classroomId);
      onInvitesChange([inv, ...invites]);
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleCopy(invite: Invite) {
    await navigator.clipboard.writeText(invite.invite_url);
    setCopiedId(invite.id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  async function handleRevoke(inviteId: string) {
    setRevokingId(inviteId);
    try {
      await revokeInvite(token, classroomId, inviteId);
      const updated = await fetchInvites(token, classroomId);
      onInvitesChange(updated.invites);
    } finally {
      setRevokingId(null);
      setConfirmRevokeId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Invite Links</h3>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary-500/10 text-primary-400 hover:bg-primary-500/20 transition-colors duration-150 disabled:opacity-50"
        >
          {isGenerating ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Plus className="w-3.5 h-3.5" />
          )}
          Generate Link
        </button>
      </div>

      {invites.length === 0 ? (
        <p className="text-xs text-text-muted py-3 text-center">
          No active invite links. Generate one to share with your students.
        </p>
      ) : (
        <div className="space-y-2">
          <AnimatePresence>
            {invites.map((inv) => (
              <motion.div
                key={inv.id}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-bg-surface border border-border-subtle"
              >
                <Link className="w-3.5 h-3.5 text-text-muted shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-mono text-text-secondary truncate">{inv.invite_url}</p>
                  <p className="text-[11px] text-text-muted">{formatExpiresAt(inv.expires_at)}</p>
                </div>
                <button
                  onClick={() => handleCopy(inv)}
                  className="shrink-0 p-1.5 rounded text-text-muted hover:text-primary-400 transition-colors"
                  title="Copy link"
                >
                  {copiedId === inv.id ? (
                    <Check className="w-3.5 h-3.5 text-success-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
                {confirmRevokeId === inv.id ? (
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => handleRevoke(inv.id)}
                      disabled={revokingId === inv.id}
                      className="text-[11px] px-2 py-1 rounded bg-danger-500/10 text-danger-400 hover:bg-danger-500/20 transition-colors"
                    >
                      {revokingId === inv.id ? "Revoking…" : "Confirm"}
                    </button>
                    <button
                      onClick={() => setConfirmRevokeId(null)}
                      className="text-[11px] px-2 py-1 rounded bg-bg-surface-raised text-text-muted hover:text-text-primary transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmRevokeId(inv.id)}
                    className="shrink-0 p-1.5 rounded text-text-muted hover:text-danger-400 transition-colors"
                    title="Revoke link"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
