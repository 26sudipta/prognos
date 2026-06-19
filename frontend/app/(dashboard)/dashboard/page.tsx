"use client";

import { useAuth } from "@/app/_components/auth-provider";
import { TrendingUp, Link2, Calendar } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary">
          Welcome back{user ? `, ${user.name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Your competitive programming dashboard is being set up.
        </p>
      </div>

      {/* Placeholder cards — Phase 2 will fill these */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <PlaceholderCard
          icon={<TrendingUp className="w-5 h-5 text-primary-400" />}
          title="Rating"
          description="Link your Codeforces handle to see your rating history and analytics."
        />
        <PlaceholderCard
          icon={<Link2 className="w-5 h-5 text-accent-400" />}
          title="Handles"
          description="Verify your Codeforces handle to start tracking your performance."
        />
        <PlaceholderCard
          icon={<Calendar className="w-5 h-5 text-success-400" />}
          title="Contests"
          description="Upcoming contests across Codeforces will appear here."
        />
      </div>

      {/* Next step prompt */}
      <div className="mt-6 p-5 bg-bg-surface border border-border-subtle rounded-xl">
        <p className="text-sm text-text-secondary">
          <span className="text-text-primary font-medium">Next step:</span>{" "}
          Go to{" "}
          <span className="text-primary-400 font-medium">Handles</span> to
          verify your Codeforces account and unlock your full dashboard.
        </p>
      </div>
    </div>
  );
}

function PlaceholderCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
      <div className="flex items-center gap-2.5 mb-3">
        {icon}
        <h2 className="text-sm font-semibold text-text-primary">{title}</h2>
      </div>
      <p className="text-xs text-text-muted leading-relaxed">{description}</p>
    </div>
  );
}
