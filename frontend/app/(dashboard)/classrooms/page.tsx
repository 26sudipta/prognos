"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, Plus, Users } from "lucide-react";
import { useAuth } from "@/app/_components/auth-provider";
import { Classroom, fetchClassrooms } from "@/app/_lib/classrooms";

function ClassroomCard({ classroom, onClick }: { classroom: Classroom; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-5 rounded-xl bg-bg-surface border border-border-subtle hover:border-primary-500/30 hover:bg-bg-surface-raised transition-colors duration-150 group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-text-primary truncate group-hover:text-primary-400 transition-colors">
            {classroom.name}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide ${
                classroom.my_role === "teacher"
                  ? "bg-primary-500/10 text-primary-400"
                  : "bg-bg-surface-raised text-text-muted"
              }`}
            >
              {classroom.my_role}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-text-muted">
          <Users className="w-3.5 h-3.5" />
          <span className="text-xs">{classroom.member_count}</span>
        </div>
      </div>
    </button>
  );
}

function ClassroomCardSkeleton() {
  return (
    <div className="p-5 rounded-xl bg-bg-surface border border-border-subtle animate-shimmer">
      <div className="h-5 w-2/3 bg-bg-surface-raised rounded mb-3" />
      <div className="h-4 w-16 bg-bg-surface-raised rounded" />
    </div>
  );
}

export default function ClassroomsPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [classrooms, setClassrooms] = useState<Classroom[] | null | undefined>(undefined);

  useEffect(() => {
    if (!token) return;
    fetchClassrooms(token)
      .then((r) => setClassrooms(r.classrooms.length > 0 ? r.classrooms : null))
      .catch(() => setClassrooms(null));
  }, [token]);

  return (
    <div className="space-y-5 max-w-[900px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-primary-400" />
            Classrooms
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Create a classroom or join one via invite link.
          </p>
        </div>
        <button
          onClick={() => router.push("/classrooms/create")}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-primary-500/10 text-primary-400 hover:bg-primary-500/20 transition-colors duration-150"
        >
          <Plus className="w-4 h-4" />
          Create Classroom
        </button>
      </div>

      {/* Content */}
      {classrooms === undefined ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <ClassroomCardSkeleton key={i} />
          ))}
        </div>
      ) : classrooms === null ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <GraduationCap className="w-10 h-10 text-text-muted mb-3 opacity-40" />
          <p className="text-sm font-medium text-text-primary mb-1">No classrooms yet</p>
          <p className="text-xs text-text-muted mb-5">
            Create one or ask your teacher for an invite link.
          </p>
          <button
            onClick={() => router.push("/classrooms/create")}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-primary-500/10 text-primary-400 hover:bg-primary-500/20 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Classroom
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {classrooms.map((c) => (
            <ClassroomCard
              key={c.id}
              classroom={c}
              onClick={() => router.push(`/classrooms/${c.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
