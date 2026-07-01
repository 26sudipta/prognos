"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, AlertCircle, LogOut, Trash2, RefreshCw } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import { updateDisplayName, logoutEverywhere, deleteAccount, UserApiError } from "@/app/_lib/users";

export default function SettingsPage() {
  const { user, token, logout, refreshUser } = useAuth();
  const router = useRouter();

  const [name, setName] = useState(user?.name ?? "");
  const [savingName, setSavingName] = useState(false);
  const [nameMsg, setNameMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const [signingOut, setSigningOut] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteErr, setDeleteErr] = useState<string | null>(null);

  const trimmed = name.trim();
  const dirty = !!user && trimmed.length > 0 && trimmed !== user.name;

  async function saveName() {
    if (!token || !dirty || savingName) return;
    setSavingName(true);
    setNameMsg(null);
    try {
      await updateDisplayName(token, trimmed);
      await refreshUser(); // keep the sidebar name in sync
      setNameMsg({ ok: true, text: "Saved" });
    } catch (e) {
      setNameMsg({ ok: false, text: e instanceof Error ? e.message : "Couldn't save" });
    } finally {
      setSavingName(false);
      setTimeout(() => setNameMsg(null), 3000);
    }
  }

  async function signOutEverywhere() {
    if (!token || signingOut) return;
    setSigningOut(true);
    try {
      await logoutEverywhere(token);
    } catch {
      // best-effort — we still drop the local session below
    }
    await logout();
    router.replace("/login");
  }

  async function onDelete() {
    if (!token || deleting) return;
    setDeleting(true);
    setDeleteErr(null);
    try {
      await deleteAccount(token);
      await logout();
      router.replace("/login");
    } catch (e) {
      setDeleteErr(
        e instanceof UserApiError && e.status === 409
          ? "You still own a classroom — delete it first, then you can delete your account."
          : e instanceof Error
          ? e.message
          : "Couldn't delete your account",
      );
      setConfirmDelete(false);
      setDeleting(false);
    }
  }

  return (
    <div className="max-w-[640px] mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
        <p className="text-sm text-text-secondary mt-1">Manage your account.</p>
      </div>

      <div className="space-y-5">
        {/* ── Profile ─────────────────────────────────────────── */}
        <section className="bg-bg-surface border border-border-subtle rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Profile</h2>

          <div className="flex items-center gap-3 mb-5">
            {user?.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={user.avatar_url} alt={user.name} className="w-11 h-11 rounded-full object-cover" />
            ) : (
              <div className="w-11 h-11 rounded-full bg-primary-600 flex items-center justify-center text-sm font-semibold text-white">
                {(user?.name ?? "?").charAt(0).toUpperCase()}
              </div>
            )}
            <div className="min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{user?.name}</p>
              <p className="text-xs text-text-muted truncate">{user?.email}</p>
            </div>
          </div>

          <label className="block text-xs font-medium text-text-secondary mb-2">Display name</label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={name}
              maxLength={255}
              onChange={(e) => setName(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-bg-base border border-border-subtle rounded-xl text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all duration-150"
            />
            <button
              onClick={saveName}
              disabled={!dirty || savingName}
              className="shrink-0 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-primary-500 text-white hover:bg-primary-400 transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {savingName ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Save"}
            </button>
          </div>
          {nameMsg && (
            <p className={`mt-2 flex items-center gap-1.5 text-xs ${nameMsg.ok ? "text-success-400" : "text-danger-400"}`}>
              {nameMsg.ok ? <Check className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
              {nameMsg.text}
            </p>
          )}
          <p className="mt-2 text-xs text-text-muted">
            Email and Codeforces handle can&apos;t be changed here — manage your handle on the{" "}
            <a href="/handles" className="text-primary-400 hover:text-primary-300">Handles</a> page.
          </p>
        </section>

        {/* ── Security ────────────────────────────────────────── */}
        <section className="bg-bg-surface border border-border-subtle rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-text-primary mb-1">Security</h2>
          <p className="text-xs text-text-muted mb-4">
            Signs you out of every device by revoking all active sessions.
          </p>
          <button
            onClick={signOutEverywhere}
            disabled={signingOut}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-text-secondary border border-border-default hover:bg-bg-surface-raised hover:text-text-primary transition-colors duration-150 disabled:opacity-50"
          >
            {signingOut ? <RefreshCw className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
            Sign out everywhere
          </button>
        </section>

        {/* ── Danger zone ─────────────────────────────────────── */}
        <section className="bg-bg-surface border border-danger-500/25 rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-danger-400 mb-1">Delete account</h2>
          <p className="text-xs text-text-muted mb-4">
            Permanently deactivates your account and removes your data. This can&apos;t be undone.
          </p>

          {deleteErr && (
            <div className="flex items-start gap-2 p-3 mb-4 bg-danger-500/8 border border-danger-500/20 rounded-xl">
              <AlertCircle className="w-4 h-4 text-danger-400 shrink-0 mt-0.5" />
              <p className="text-sm text-danger-400">{deleteErr}</p>
            </div>
          )}

          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-danger-400 border border-danger-500/30 hover:bg-danger-500/10 transition-colors duration-150"
            >
              <Trash2 className="w-4 h-4" />
              Delete my account
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={onDelete}
                disabled={deleting}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-danger-500 text-white hover:bg-danger-600 transition-colors duration-150 disabled:opacity-50"
              >
                {deleting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                Yes, delete permanently
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                disabled={deleting}
                className="px-4 py-2.5 rounded-xl text-sm text-text-muted hover:text-text-primary transition-colors duration-150"
              >
                Cancel
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
