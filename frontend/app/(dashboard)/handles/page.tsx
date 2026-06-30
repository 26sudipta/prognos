"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Check,
  Copy,
  ExternalLink,
  Link2,
  Lock,
  AlertCircle,
  ArrowRight,
  Unlink,
  Shield,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import {
  ApiError,
  fetchHandles,
  initiateVerification,
  confirmVerification,
  unlinkHandle,
  syncHandle,
} from "@/app/_lib/handles";

// ─── State machine ───────────────────────────────────────────────────────────

type WizardState =
  | { status: "LOADING" }
  | { status: "NO_HANDLE"; error?: string }
  | {
      status: "PENDING";
      handleId: string;
      handle: string;
      token: string;
      expiresAt: Date;
    }
  | {
      status: "FAILED";
      handleId: string;
      handle: string;
      token: string;
      expiresAt: Date;
      attemptsRemaining: number;
    }
  | {
      status: "LOCKED";
      handleId: string;
      handle: string;
      lockoutExpiresAt: Date;
    }
  | { status: "SUCCESS"; handle: string; handleId: string; verifiedAt: Date };

function currentStep(state: WizardState): 1 | 2 | 3 {
  if (state.status === "NO_HANDLE" || state.status === "LOADING") return 1;
  if (state.status === "SUCCESS") return 3;
  return 2;
}

// ─── Countdown hook ───────────────────────────────────────────────────────────

function useCountdown(target: Date | null): string {
  const [display, setDisplay] = useState("");

  useEffect(() => {
    if (!target) return;
    const tick = () => {
      const diff = target.getTime() - Date.now();
      if (diff <= 0) { setDisplay("00:00"); return; }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setDisplay(`${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [target]);

  return display;
}

// ─── Step indicator ───────────────────────────────────────────────────────────

const STEPS = ["Enter Handle", "Copy Token", "Verify"] as const;

function StepIndicator({ step }: { step: 1 | 2 | 3 }) {
  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((label, i) => {
        const n = (i + 1) as 1 | 2 | 3;
        const done = n < step;
        const active = n === step;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300 ${
                  done
                    ? "bg-success-500 text-white"
                    : active
                    ? "bg-primary-500 text-white ring-4 ring-primary-500/20"
                    : "bg-bg-surface-raised border border-border-subtle text-text-disabled"
                }`}
              >
                {done ? <Check className="w-3.5 h-3.5" strokeWidth={2.5} /> : n}
              </div>
              <span
                className={`text-xs font-medium whitespace-nowrap transition-colors duration-300 ${
                  done
                    ? "text-success-500"
                    : active
                    ? "text-text-primary"
                    : "text-text-disabled"
                }`}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`w-16 h-px mx-2 mb-5 transition-colors duration-500 ${
                  n < step ? "bg-success-500/40" : "bg-border-subtle"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Token display ────────────────────────────────────────────────────────────

function TokenDisplay({ token }: { token: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="relative flex items-center justify-between px-4 py-3.5 bg-bg-base rounded-xl border border-border-default group">
      <span className="font-mono text-xl font-semibold text-text-primary tracking-widest select-none">
        {token}
      </span>
      <button
        onClick={copy}
        className={`ml-4 shrink-0 flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg transition-all duration-150 ${
          copied
            ? "bg-success-500/15 text-success-400"
            : "bg-bg-surface-raised text-text-secondary hover:text-text-primary hover:bg-bg-surface-overlay"
        }`}
        title="Copy token"
      >
        <AnimatePresence mode="wait" initial={false}>
          {copied ? (
            <motion.span
              key="check"
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.6, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
              Copied
            </motion.span>
          ) : (
            <motion.span
              key="copy"
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.6, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="flex items-center gap-1.5"
            >
              <Copy className="w-3.5 h-3.5" />
              Copy
            </motion.span>
          )}
        </AnimatePresence>
      </button>
    </div>
  );
}

// ─── Verify polling config ──────────────────────────────────────────────────
// One "Verify" click patiently re-checks Codeforces several times, spaced apart, so a
// user who clicks before CF reflects their Organization field still succeeds without
// having to babysit it. A progress bar keeps them from leaving mid-wait.
const VERIFY_ATTEMPTS = 5;
const VERIFY_INTERVAL_MS = 30_000;

type VerifyProgress = {
  attempt: number;
  total: number;
  pct: number;
  phase: "checking" | "waiting";
  secondsToNext: number;
};

// ─── Main page ────────────────────────────────────────────────────────────────

export default function HandlesPage() {
  const { token: authToken } = useAuth();
  const router = useRouter();
  const [state, setState] = useState<WizardState>({ status: "LOADING" });
  const [handleInput, setHandleInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  // Transient confirm error (gateway timeout / 5xx / network) — distinct from a real
  // token mismatch. We keep the user on the Verify step with their token intact instead
  // of wrongly telling them "no attempts remaining."
  const [confirmError, setConfirmError] = useState<string | null>(null);
  // Live progress for the patient multi-attempt verify; null when not verifying.
  const [verifyProgress, setVerifyProgress] = useState<VerifyProgress | null>(null);
  const verifyCancelRef = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Determine countdown target based on state
  const countdownTarget =
    state.status === "PENDING" || state.status === "FAILED"
      ? state.expiresAt
      : state.status === "LOCKED"
      ? state.lockoutExpiresAt
      : null;
  const countdown = useCountdown(countdownTarget);

  // Load existing handle state on mount
  useEffect(() => {
    if (!authToken) return;
    fetchHandles(authToken)
      .then((handles) => {
        const cf = handles.find((h) => h.platform === "codeforces");
        if (!cf) { setState({ status: "NO_HANDLE" }); return; }

        if (cf.is_verified) {
          setState({
            status: "SUCCESS",
            handle: cf.handle,
            handleId: cf.id,
            verifiedAt: new Date(cf.verified_at!),
          });
          return;
        }

        if (cf.is_locked && cf.lockout_expires_at) {
          const lockoutExpiry = new Date(cf.lockout_expires_at);
          if (lockoutExpiry > new Date()) {
            setState({
              status: "LOCKED",
              handleId: cf.id,
              handle: cf.handle,
              lockoutExpiresAt: lockoutExpiry,
            });
            return;
          }
        }

        // Unverified, not locked, but a token is still alive → resume the Verify step
        // with the SAME token (survives refresh, no new token minted).
        if (cf.verification_token && cf.verification_token_expires_at) {
          const tokenExpiry = new Date(cf.verification_token_expires_at);
          if (tokenExpiry > new Date()) {
            setState({
              status: "PENDING",
              handleId: cf.id,
              handle: cf.handle,
              token: cf.verification_token,
              expiresAt: tokenExpiry,
            });
            return;
          }
        }

        // Unverified, no live token → fresh start
        setState({ status: "NO_HANDLE" });
      })
      .catch(() => setState({ status: "NO_HANDLE" }));
  }, [authToken]);

  // Auto-focus input when on NO_HANDLE
  useEffect(() => {
    if (state.status === "NO_HANDLE") {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [state.status]);

  // Stop any in-flight verify loop if the user navigates away mid-wait.
  useEffect(() => () => { verifyCancelRef.current = true; }, []);

  // Token expiry: once the countdown hits 0 the token is dead — block the Verify click
  // (it would just 410) and point the user at "Start over". `countdown` re-renders us each
  // second, so this stays current.
  const tokenExpired =
    (state.status === "PENDING" || state.status === "FAILED") &&
    state.expiresAt.getTime() <= Date.now();

  async function handleInitiate(e: React.FormEvent) {
    e.preventDefault();
    if (!authToken || !handleInput.trim()) return;
    setSubmitting(true);
    try {
      const data = await initiateVerification(authToken, handleInput.trim());
      setState({
        status: "PENDING",
        handleId: data.handle_id,
        handle: data.handle,
        token: data.token,
        expiresAt: new Date(data.expires_at),
      });
      setHandleInput("");
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 409
            ? "This handle is already claimed by another account."
            : err.status === 404
            ? "Handle not found on Codeforces. Check the spelling."
            : err.status === 423
            ? "Handle is locked due to too many failed attempts."
            : err.message
          : "Something went wrong. Please try again.";
      setState({ status: "NO_HANDLE", error: msg });
    } finally {
      setSubmitting(false);
    }
  }

  function cancelVerify() {
    verifyCancelRef.current = true;
  }

  async function handleConfirm() {
    if (!authToken || (state.status !== "PENDING" && state.status !== "FAILED")) return;
    // Capture now — `state` is PENDING|FAILED here and won't change during the loop.
    const { handleId, handle, token, expiresAt } = state;

    setSubmitting(true);
    setConfirmError(null);
    verifyCancelRef.current = false;

    const startedAt = Date.now();
    // Rough window for the progress bar: the inter-attempt waits dominate.
    const windowMs = (VERIFY_ATTEMPTS - 1) * VERIFY_INTERVAL_MS + VERIFY_ATTEMPTS * 8000;
    const pctNow = () => Math.min(95, Math.round(((Date.now() - startedAt) / windowMs) * 100));

    try {
      for (let i = 0; i < VERIFY_ATTEMPTS; i++) {
        if (verifyCancelRef.current) return;
        setVerifyProgress({ attempt: i + 1, total: VERIFY_ATTEMPTS, pct: pctNow(), phase: "checking", secondsToNext: 0 });

        try {
          const data = await confirmVerification(authToken, handleId);
          setVerifyProgress({ attempt: i + 1, total: VERIFY_ATTEMPTS, pct: 100, phase: "checking", secondsToNext: 0 });
          setState({
            status: "SUCCESS",
            handle: data.handle,
            handleId: data.handle_id,
            verifiedAt: new Date(data.verified_at),
          });
          return;
        } catch (err) {
          // Terminal outcomes — stop the loop immediately.
          if (err instanceof ApiError && err.status === 410) {
            setState({ status: "NO_HANDLE", error: "Your token expired. Enter your handle again to get a fresh one." });
            return;
          }
          if (err instanceof ApiError && err.status === 423) {
            setState({ status: "LOCKED", handleId, handle, lockoutExpiresAt: new Date(Date.now() + 15 * 60 * 1000) });
            return;
          }

          const isMismatch = err instanceof ApiError && err.status === 400;

          // Out of attempts → surface the outcome.
          if (i === VERIFY_ATTEMPTS - 1) {
            if (isMismatch) {
              setState({ status: "FAILED", handleId, handle, token, expiresAt, attemptsRemaining: 0 });
            } else {
              setConfirmError(
                "Couldn't reach Codeforces just now — your token is still valid. Wait a moment and verify again.",
              );
            }
            return;
          }

          // Otherwise it's "not propagated yet" (or a transient blip) — wait, then re-check.
          const waitUntil = Date.now() + VERIFY_INTERVAL_MS;
          while (Date.now() < waitUntil) {
            if (verifyCancelRef.current) return;
            setVerifyProgress({
              attempt: i + 1,
              total: VERIFY_ATTEMPTS,
              pct: pctNow(),
              phase: "waiting",
              secondsToNext: Math.ceil((waitUntil - Date.now()) / 1000),
            });
            await new Promise((r) => setTimeout(r, 1000));
          }
        }
      }
    } finally {
      setVerifyProgress(null);
      setSubmitting(false);
    }
  }

  async function handleSync() {
    if (!authToken || state.status !== "SUCCESS") return;
    setSyncing(true);
    try {
      await syncHandle(authToken, state.handleId);
    } catch {
      // silently ignore — sync may already be running
    } finally {
      setSyncing(false);
    }
    router.push("/dashboard");
  }

  async function handleUnlink() {
    if (!authToken || state.status !== "SUCCESS") return;
    setSubmitting(true);
    try {
      const handles = await fetchHandles(authToken);
      const cf = handles.find((h) => h.platform === "codeforces");
      if (cf) await unlinkHandle(authToken, cf.id);
      setState({ status: "NO_HANDLE" });
    } catch {
      // silently ignore — user can retry
    } finally {
      setSubmitting(false);
    }
  }

  function startOver() {
    verifyCancelRef.current = true;
    setVerifyProgress(null);
    setConfirmError(null);
    setHandleInput(
      state.status === "PENDING" || state.status === "FAILED" ? state.handle : "",
    );
    setState({ status: "NO_HANDLE" });
  }

  const step = currentStep(state);

  return (
    <div className="max-w-5xl mx-auto">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary">Handles</h1>
        <p className="text-sm text-text-secondary mt-1">
          Link and verify your competitive programming accounts.
        </p>
      </div>

      <div className="max-w-[480px]">
        <AnimatePresence mode="wait">
          {/* ── LOADING ─────────────────────────────────────────────────── */}
          {state.status === "LOADING" && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col gap-3"
            >
              <div className="skeleton h-5 w-32 rounded-lg" />
              <div className="skeleton h-[280px] rounded-xl" />
            </motion.div>
          )}

          {/* ── SUCCESS ─────────────────────────────────────────────────── */}
          {state.status === "SUCCESS" && (
            <motion.div
              key="success"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="bg-bg-surface border border-border-subtle rounded-2xl p-7"
            >
              {/* Checkmark burst */}
              <div className="flex justify-center mb-6">
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1, type: "spring", stiffness: 260, damping: 18 }}
                  className="w-14 h-14 rounded-full bg-success-500/15 flex items-center justify-center"
                >
                  <Check className="w-7 h-7 text-success-400" strokeWidth={2.5} />
                </motion.div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-center"
              >
                <h2 className="text-xl font-bold text-text-primary mb-1">Handle verified.</h2>
                <p className="text-sm text-text-muted mb-6">
                  Codeforces · Verified{" "}
                  {state.verifiedAt.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>

                {/* Handle badge */}
                <div className="flex items-center justify-between px-4 py-3 bg-bg-base rounded-xl border border-border-subtle mb-6">
                  <span className="font-mono text-lg font-semibold text-text-primary tracking-wide">
                    {state.handle}
                  </span>
                  <span className="flex items-center gap-1.5 text-xs font-medium text-success-400 bg-success-500/10 px-2.5 py-1 rounded-full">
                    <Check className="w-3 h-3" strokeWidth={3} />
                    verified
                  </span>
                </div>

                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold bg-primary-500 text-white hover:bg-primary-400 transition-colors duration-150 mb-3 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {syncing ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      Sync &amp; Go to Dashboard
                    </>
                  )}
                </button>

                <button
                  onClick={handleUnlink}
                  disabled={submitting || syncing}
                  className="text-xs text-text-muted hover:text-danger-400 transition-colors duration-150 disabled:opacity-40"
                >
                  Unlink handle
                </button>
              </motion.div>
            </motion.div>
          )}

          {/* ── WIZARD (NO_HANDLE / PENDING / FAILED / LOCKED) ─────────── */}
          {(state.status === "NO_HANDLE" ||
            state.status === "PENDING" ||
            state.status === "FAILED" ||
            state.status === "LOCKED") && (
            <motion.div
              key="wizard"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="bg-bg-surface border border-border-subtle rounded-2xl p-7"
            >
              <StepIndicator step={step} />

              <AnimatePresence mode="wait">

                {/* ── Step 1: Enter handle ─────────────────────────────── */}
                {state.status === "NO_HANDLE" && (
                  <motion.div
                    key="step1"
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 16 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="mb-6">
                      <h2 className="text-lg font-semibold text-text-primary mb-1">
                        Link your Codeforces account
                      </h2>
                      <p className="text-sm text-text-secondary">
                        Verify ownership to unlock your full dashboard.
                      </p>
                    </div>

                    <form onSubmit={handleInitiate} className="space-y-5">
                      <div>
                        <label className="block text-xs font-medium text-text-secondary mb-2">
                          Codeforces handle
                        </label>
                        <input
                          ref={inputRef}
                          type="text"
                          value={handleInput}
                          onChange={(e) => setHandleInput(e.target.value)}
                          placeholder="tourist"
                          spellCheck={false}
                          autoComplete="off"
                          className="w-full px-4 py-3 bg-bg-base border border-border-subtle rounded-xl font-mono text-text-primary placeholder:text-text-disabled text-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all duration-150"
                        />
                      </div>

                      {/* Error from initiate */}
                      {state.error && (
                        <motion.div
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="flex items-start gap-2.5 p-3 bg-danger-500/8 border border-danger-500/20 rounded-xl"
                        >
                          <AlertCircle className="w-4 h-4 text-danger-400 shrink-0 mt-0.5" />
                          <p className="text-sm text-danger-400">{state.error}</p>
                        </motion.div>
                      )}

                      <button
                        type="submit"
                        disabled={submitting || !handleInput.trim()}
                        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold bg-primary-500 text-white hover:bg-primary-400 active:scale-[0.98] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100"
                      >
                        {submitting ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            Continue
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    </form>

                    {/* What happens explanation */}
                    <div className="mt-6 pt-5 border-t border-border-subtle">
                      <p className="text-xs text-text-muted mb-3 font-medium">How verification works</p>
                      <ol className="space-y-2.5">
                        {[
                          "We check the handle exists on Codeforces.",
                          "You paste a short token into the Organization field at codeforces.com/settings/social. Remove it after verification.",
                          "We read it back — this proves you own the account.",
                        ].map((step, i) => (
                          <li key={i} className="flex items-start gap-2.5 text-xs text-text-muted">
                            <span className="w-4 h-4 rounded-full bg-bg-surface-raised border border-border-subtle flex items-center justify-center text-[10px] font-semibold text-text-disabled shrink-0 mt-0.5">
                              {i + 1}
                            </span>
                            {step}
                          </li>
                        ))}
                      </ol>
                    </div>
                  </motion.div>
                )}

                {/* ── Steps 2+3: Token + Verify ────────────────────────── */}
                {(state.status === "PENDING" ||
                  state.status === "FAILED" ||
                  state.status === "LOCKED") && (
                  <motion.div
                    key="step2"
                    initial={{ opacity: 0, x: 16 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -16 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="mb-4">
                      <h2 className="text-lg font-semibold text-text-primary mb-1">
                        Paste this token into your CF profile
                      </h2>
                      <p className="text-sm text-text-secondary">
                        Go to{" "}
                        <a
                          href="https://codeforces.com/settings/social"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-400 hover:text-primary-300 inline-flex items-center gap-1 transition-colors"
                        >
                          codeforces.com/settings/social
                          <ExternalLink className="w-3 h-3" />
                        </a>
                        , paste the token below into the{" "}
                        <span className="text-text-primary font-medium">Organization</span> field, and
                        click <span className="text-text-primary font-medium">Save changes</span>.
                      </p>
                    </div>

                    {/* Which account is being verified — confirm it's the right one */}
                    {state.status !== "LOCKED" && (
                      <div className="flex items-center justify-between gap-2 mb-4 px-3 py-2 bg-bg-base rounded-lg border border-border-subtle">
                        <span className="text-xs text-text-muted">
                          Verifying account{" "}
                          <a
                            href={`https://codeforces.com/profile/${state.handle}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono font-medium text-text-secondary hover:text-primary-300 transition-colors"
                          >
                            {state.handle}
                          </a>
                        </span>
                        <button
                          onClick={startOver}
                          className="text-[11px] text-text-disabled hover:text-text-secondary transition-colors shrink-0"
                        >
                          Wrong handle?
                        </button>
                      </div>
                    )}

                    {/* "Open new tab" hint */}
                    <div className="flex items-center gap-2 mb-4 text-xs text-warning-400">
                      <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      Open a new tab — keep this page open.
                    </div>

                    {/* Token */}
                    {state.status !== "LOCKED" && (
                      <div className="mb-4">
                        <TokenDisplay token={state.token} />
                      </div>
                    )}

                    {/* Locked: show handle instead */}
                    {state.status === "LOCKED" && (
                      <div className="mb-4 flex items-center gap-2.5 px-4 py-3 bg-bg-base rounded-xl border border-border-subtle">
                        <Lock className="w-4 h-4 text-warning-400 shrink-0" />
                        <span className="font-mono text-sm text-text-secondary">{state.handle}</span>
                      </div>
                    )}

                    {/* Expiry countdown (only when not locked) */}
                    {(state.status === "PENDING" || state.status === "FAILED") && (
                      <p className="text-xs text-text-muted mb-5">
                        Token expires in{" "}
                        <span className="font-mono text-text-secondary">{countdown}</span>
                      </p>
                    )}

                    {/* LOCKED: countdown + message */}
                    {state.status === "LOCKED" && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-5"
                      >
                        <div className="flex items-center justify-between px-4 py-3.5 bg-warning-500/8 border border-warning-500/20 rounded-xl mb-3">
                          <div className="flex items-center gap-2.5">
                            <Lock className="w-4 h-4 text-warning-400 shrink-0" />
                            <span className="text-sm text-warning-400 font-medium">Try again in</span>
                          </div>
                          <span className="font-mono text-lg font-semibold text-warning-400 tabular-nums">
                            {countdown}
                          </span>
                        </div>
                        <p className="text-xs text-text-muted">
                          Too many failed attempts. Your token is still valid — try again after the cooldown.
                        </p>
                      </motion.div>
                    )}

                    {/* FAILED: error message */}
                    {state.status === "FAILED" && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-start gap-2.5 p-3 bg-danger-500/8 border border-danger-500/20 rounded-xl mb-5"
                      >
                        <AlertCircle className="w-4 h-4 text-danger-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm text-danger-400">
                            Still can&apos;t see the token in your Codeforces Organization field.
                          </p>
                          <p className="text-xs text-text-muted mt-0.5">
                            We re-checked for ~2 minutes and still didn&apos;t see it. Open{" "}
                            <a
                              href="https://codeforces.com/settings/social"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-text-secondary underline hover:text-text-primary"
                            >
                              settings/social
                            </a>
                            , paste the token into the <span className="text-text-secondary">Organization</span> field,
                            click <span className="text-text-secondary">Save changes</span>, then hit Verify again.
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {/* Transient (non-mismatch) confirm error — token stays valid */}
                    {confirmError && state.status !== "LOCKED" && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-start gap-2.5 p-3 bg-warning-500/8 border border-warning-500/20 rounded-xl mb-5"
                      >
                        <AlertCircle className="w-4 h-4 text-warning-400 shrink-0 mt-0.5" />
                        <p className="text-sm text-warning-400">{confirmError}</p>
                      </motion.div>
                    )}

                    {/* Patient verify progress — one click, several spaced re-checks */}
                    {verifyProgress && state.status !== "LOCKED" ? (
                      <div className="space-y-3">
                        <div className="px-4 py-4 bg-bg-base rounded-xl border border-border-default">
                          <div className="flex items-baseline justify-between mb-2">
                            <span className="text-sm font-medium text-text-primary flex items-center gap-2">
                              <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary-400" />
                              {verifyProgress.phase === "checking"
                                ? "Checking Codeforces…"
                                : `Waiting for Codeforces — next check in ${verifyProgress.secondsToNext}s`}
                            </span>
                            <span className="font-mono text-lg font-semibold text-primary-400 tabular-nums">
                              {verifyProgress.pct}%
                            </span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-bg-surface-raised overflow-hidden">
                            <motion.div
                              className="h-full bg-primary-500 rounded-full"
                              animate={{ width: `${verifyProgress.pct}%` }}
                              transition={{ ease: "linear", duration: 0.4 }}
                            />
                          </div>
                          <p className="text-xs text-text-muted mt-2">
                            Attempt {verifyProgress.attempt} of {verifyProgress.total} · CF can take a minute to
                            update — hang tight, we&apos;ll keep checking.
                          </p>
                        </div>
                        <button
                          onClick={cancelVerify}
                          className="w-full py-2.5 rounded-xl text-sm text-text-muted hover:text-text-primary hover:bg-bg-surface-raised transition-all duration-150"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {state.status !== "LOCKED" && (
                          <>
                            <button
                              onClick={handleConfirm}
                              disabled={submitting || tokenExpired}
                              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold bg-primary-500 text-white hover:bg-primary-400 active:scale-[0.98] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100"
                            >
                              <Shield className="w-4 h-4" />
                              I&apos;ve done it — Verify
                            </button>
                            {tokenExpired && (
                              <p className="text-xs text-warning-400 text-center">
                                This token expired. Hit &ldquo;Start over&rdquo; for a fresh one.
                              </p>
                            )}
                          </>
                        )}

                        <button
                          onClick={startOver}
                          disabled={submitting}
                          className="w-full py-2.5 rounded-xl text-sm text-text-muted hover:text-text-primary hover:bg-bg-surface-raised transition-all duration-150 disabled:opacity-40"
                        >
                          Start over
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}

              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Security note — shown below wizard in all non-loading states */}
        {state.status !== "LOADING" && state.status !== "SUCCESS" && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-4 text-center text-xs text-text-disabled"
          >
            We never store your Codeforces password. Verification uses a one-time token only.
          </motion.p>
        )}
      </div>
    </div>
  );
}
