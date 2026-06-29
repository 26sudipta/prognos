"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import { createClassroom } from "@/app/_lib/classrooms";

export default function CreateClassroomPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = name.trim();
  const isValid = trimmed.length >= 1 && trimmed.length <= 255;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !isValid || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const classroom = await createClassroom(token, trimmed);
      router.replace(`/classrooms/${classroom.id}`);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setError(msg);
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-[500px] mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push("/classrooms")}
          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-surface-raised transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-text-primary">Create a Classroom</h1>
          <p className="text-xs text-text-muted mt-0.5">
            You&apos;ll be assigned as the teacher automatically.
          </p>
        </div>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="p-5 rounded-xl bg-bg-surface border border-border-subtle space-y-4"
      >
        <div>
          <label htmlFor="classroom-name" className="block text-xs font-medium text-text-muted mb-1.5">
            Classroom Name
          </label>
          <input
            id="classroom-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. ICPC Team 2026"
            maxLength={255}
            autoFocus
            className="w-full px-3 py-2.5 rounded-lg bg-bg-base border border-border-subtle text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/30 transition-colors"
          />
          <p className="text-[11px] text-text-muted mt-1">
            {trimmed.length}/255 characters
          </p>
        </div>

        {error && (
          <p className="text-xs text-danger-400 bg-danger-500/10 border border-danger-500/20 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!isValid || isSubmitting}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            Create Classroom
          </button>
        </div>
      </form>
    </div>
  );
}
