"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2 } from "lucide-react";

interface CFUser {
  handle: string;
  rank: string;
  rating: number;
  maxRating: number;
  titlePhoto: string;
}

interface CFApiResponse {
  status: string;
  result?: CFUser[];
  comment?: string;
}

function getRatingColor(rating: number): string {
  if (rating >= 2400) return "#F44336";
  if (rating >= 2100) return "#FF8F00";
  if (rating >= 1900) return "#AA46BE";
  if (rating >= 1600) return "#1E88E5";
  if (rating >= 1400) return "#22D3EE";
  if (rating >= 1200) return "#4CAF50";
  return "#9E9E9E";
}

function toTitleCase(s: string): string {
  return s
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function HandlePreviewWidget() {
  const [handle, setHandle] = useState("");
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<CFUser | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function fetchPreview() {
    const h = handle.trim();
    if (!h) return;

    setLoading(true);
    setUser(null);
    setError(null);

    try {
      const res = await fetch(
        `https://codeforces.com/api/user.info?handles=${encodeURIComponent(h)}&checkHistoricHandles=false`
      );
      const data: CFApiResponse = await res.json();

      if (data.status === "OK" && data.result && data.result.length > 0) {
        setUser(data.result[0]);
      } else {
        setError("Handle not found on Codeforces.");
      }
    } catch {
      setError("Could not reach Codeforces. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") fetchPreview();
  }

  return (
    <div className="w-full max-w-lg">
      {/* Input row */}
      <div className="flex gap-2">
        <input
          type="text"
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Your Codeforces handle  (e.g. tourist)"
          className="flex-1 px-4 py-3 rounded-xl bg-bg-surface border border-border-default text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:border-primary-500 transition-colors"
        />
        <button
          onClick={fetchPreview}
          disabled={loading || !handle.trim()}
          className="flex items-center gap-2 px-5 py-3 rounded-xl bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              Preview
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="mt-4 p-4 rounded-xl bg-bg-surface border border-border-subtle flex items-center gap-4">
          <div className="skeleton w-14 h-14 rounded-full shrink-0" />
          <div className="flex-1 space-y-2.5">
            <div className="skeleton h-4 w-28 rounded" />
            <div className="skeleton h-3 w-40 rounded" />
            <div className="skeleton h-3 w-24 rounded" />
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <p className="mt-3 text-sm text-danger-400 flex items-center gap-1.5">
          <span aria-hidden>⚠</span>
          {error}
        </p>
      )}

      {/* Result card */}
      {user && !loading && (
        <div className="mt-4 rounded-xl bg-bg-surface border border-border-subtle overflow-hidden">
          <div className="p-4 flex items-center gap-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={user.titlePhoto}
              alt={user.handle}
              className="w-14 h-14 rounded-full object-cover shrink-0 border-2"
              style={{ borderColor: getRatingColor(user.rating) }}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="text-base font-bold truncate"
                  style={{ color: getRatingColor(user.rating) }}
                >
                  {user.handle}
                </span>
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-semibold shrink-0"
                  style={{
                    background: getRatingColor(user.rating) + "22",
                    color: getRatingColor(user.rating),
                  }}
                >
                  {user.rating}
                </span>
              </div>
              <p className="text-sm text-text-secondary mt-0.5">
                {toTitleCase(user.rank)}
              </p>
              <p className="text-xs text-text-muted mt-0.5">
                Peak: {user.maxRating}
              </p>
            </div>
          </div>

          <div className="border-t border-border-subtle px-4 py-3">
            <Link
              href="/login"
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-primary-500/10 text-primary-400 text-sm font-medium hover:bg-primary-500/20 transition-colors border border-primary-500/20"
            >
              Sign in with Google to unlock your full dashboard
              <ArrowRight className="w-4 h-4 shrink-0" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
