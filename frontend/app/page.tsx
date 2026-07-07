"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Users,
  Activity,
  Tag,
  Trophy,
  PieChart,
  Smartphone,
  CheckCircle,
  Brain,
  Zap,
  BarChart3,
  Sparkles,
  Play,
  Download,
} from "lucide-react";
import LandingNavbar from "@/app/_components/landing-navbar";
import HandlePreviewWidget from "@/app/_components/handle-preview-widget";

// Fixed heatmap pattern for the phone mockup (avoids hydration mismatch)
const PHONE_HEATMAP = [
  0.8, 0.1, 0.7, 0.9, 0.1, 0.8, 0.2,
  0.1, 0.9, 0.6, 0.1, 0.7, 0.9, 0.8,
  0.7, 0.1, 0.5, 0.8, 0.9, 0.1, 0.7,
  0.2, 0.8, 0.9, 0.7, 0.1, 0.8, 0.9,
  0.9, 0.1, 0.7, 0.8, 0.1, 0.9, 0.8,
];

function getRatingColor(rating: number): string {
  if (rating >= 2400) return "#F44336";
  if (rating >= 2100) return "#FF8F00";
  if (rating >= 1900) return "#AA46BE";
  if (rating >= 1600) return "#1E88E5";
  if (rating >= 1400) return "#22D3EE";
  if (rating >= 1200) return "#4CAF50";
  return "#9E9E9E";
}

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const staggerChildren = {
  show: { transition: { staggerChildren: 0.1 } },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-base text-text-primary overflow-x-hidden">
      <LandingNavbar />

      {/* ─────────────────────────── HERO ─────────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center pt-16 pb-28 px-4">
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
          <div
            className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full opacity-[0.07]"
            style={{
              background:
                "radial-gradient(circle, #6366F1 0%, #06B6D4 50%, transparent 70%)",
              filter: "blur(100px)",
            }}
          />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Category badge */}
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-medium mb-7">
              <Activity className="w-3.5 h-3.5" />
              Strava for Competitive Programming
            </span>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-text-primary tracking-tight leading-[1.1] mb-5">
              Train Like a Competitor.{" "}
              <span
                className="text-transparent bg-clip-text"
                style={{
                  backgroundImage:
                    "linear-gradient(135deg, #818CF8 0%, #22D3EE 100%)",
                }}
              >
                Know Exactly Where You Stand.
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto mb-10">
              PROGNOS turns your Codeforces history into a living dashboard —
              streak tracking, tag analytics, and classroom leaderboards for CP
              teams.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex flex-col items-center gap-4"
          >
            <HandlePreviewWidget />
            <p className="text-sm text-text-muted">
              or{" "}
              <Link
                href="/login"
                className="text-primary-400 hover:text-primary-300 underline underline-offset-2 transition-colors"
              >
                set up a classroom
              </Link>
            </p>
          </motion.div>
        </div>
      </section>

      {/* ──────────────────── INDIVIDUAL FEATURES ─────────────────── */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            className="text-center mb-14"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4">
              Everything your practice needs
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              Aggregated from your Codeforces history automatically — no manual
              input, no spreadsheets.
            </p>
          </motion.div>

          <motion.div
            variants={staggerChildren}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-60px" }}
            className="grid sm:grid-cols-3 gap-4"
          >
            {[
              {
                icon: Activity,
                title: "Submission Heatmap",
                desc: "52 weeks of practice, visualized. See every day you solved a problem and protect your streak.",
                color: "#818CF8",
              },
              {
                icon: TrendingUp,
                title: "Rating Trajectory",
                desc: "Your full Codeforces rating history, charted. See exactly when you improved and which contests moved the needle.",
                color: "#22D3EE",
              },
              {
                icon: Tag,
                title: "Tag Weakness Analysis",
                desc: "Know which problem tags are holding back your rating before they cost you a contest placement.",
                color: "#34D399",
              },
            ].map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                className="p-6 rounded-2xl bg-bg-surface border border-border-subtle hover:border-border-default transition-colors"
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: feature.color + "22" }}
                >
                  <feature.icon
                    className="w-5 h-5"
                    style={{ color: feature.color }}
                  />
                </div>
                <h3 className="text-base font-semibold text-text-primary mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {feature.desc}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ──────────────────── CLASSROOM FEATURES ──────────────────── */}
      <section
        id="classrooms"
        className="py-24 px-4 bg-bg-surface border-y border-border-subtle"
      >
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            className="text-center mb-14"
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-500/10 border border-accent-500/20 text-accent-400 text-xs font-medium mb-5">
              <Users className="w-3.5 h-3.5" />
              For CP Teams &amp; Classrooms
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4">
              Social accountability that actually works
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              Seeing a peer&apos;s daily streak and tag coverage motivates
              consistent practice far more than a personal dashboard alone.
            </p>
          </motion.div>

          <motion.div
            variants={staggerChildren}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-60px" }}
            className="grid sm:grid-cols-2 gap-6 mb-10"
          >
            {[
              {
                icon: Trophy,
                title: "Live Classroom Leaderboard",
                desc: "Create a classroom in 30 seconds. Students join by CF handle. Rankings update automatically after every sync.",
                color: "#FBBF24",
              },
              {
                icon: PieChart,
                title: "Cohort Analytics",
                desc: "See who is active, who is falling behind, and which tags the whole team needs to drill — in one teacher dashboard.",
                color: "#818CF8",
              },
            ].map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                className="p-8 rounded-2xl bg-bg-base border border-border-subtle hover:border-border-default transition-colors"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-5"
                  style={{ background: feature.color + "22" }}
                >
                  <feature.icon
                    className="w-6 h-6"
                    style={{ color: feature.color }}
                  />
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {feature.desc}
                </p>
              </motion.div>
            ))}
          </motion.div>

          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="text-center"
          >
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-7 py-3 rounded-xl bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
            >
              <Users className="w-4 h-4" />
              Create a Classroom
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ──────────────────────── MOBILE APP ──────────────────────── */}
      <section id="mobile" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Text side */}
            <motion.div
              initial={{ opacity: 0, x: -24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-success-500/10 border border-success-500/20 text-success-400 text-xs font-medium mb-6">
                <Smartphone className="w-3.5 h-3.5" />
                Mobile App
              </span>

              <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4 leading-tight">
                PROGNOS on the Go{" "}
                <span className="text-text-secondary">
                  — Now on Android
                </span>
              </h2>
              <p className="text-text-secondary mb-8 leading-relaxed">
                Contest alarms, quick-view dashboard, and offline access —
                practice tracking that lives in your pocket, everywhere you
                compete. Download the Android beta now; iOS is on the way.
              </p>

              <ul className="space-y-3 mb-10">
                {[
                  "Contest discovery with one-tap alarms",
                  "Quick-view dashboard — rating, streak, next contest",
                  "Offline access to your practice history",
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-3 text-sm text-text-secondary"
                  >
                    <CheckCircle className="w-4 h-4 text-success-400 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>

              {/* Primary: direct APK download */}
              <a
                href="/prognos.apk"
                download
                className="inline-flex items-center gap-3 px-6 py-4 mb-4 rounded-xl bg-primary-500 hover:bg-primary-600 text-white font-semibold shadow-lg shadow-primary-500/20 transition-colors"
              >
                <Download className="w-5 h-5 shrink-0" />
                <span>
                  Download for Android
                  <span className="block text-xs font-normal text-white/70">
                    Free APK · Android 6.0+ · ~40&nbsp;MB
                  </span>
                </span>
              </a>
              <p className="text-xs text-text-muted mb-6">
                A beta build — you may need to allow installs from your browser
                in Android settings.
              </p>

              {/* Store badges */}
              <div className="flex flex-wrap gap-3">
                {/* App Store */}
                <div
                  className="flex items-center gap-3 px-5 py-3 rounded-xl border border-border-default bg-bg-surface cursor-not-allowed opacity-50 select-none"
                  title="Coming soon"
                >
                  <svg
                    className="w-5 h-5 text-text-primary shrink-0"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    aria-hidden
                  >
                    <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
                  </svg>
                  <div>
                    <p className="text-[10px] text-text-muted leading-none">
                      Download on the
                    </p>
                    <p className="text-sm font-semibold text-text-primary">
                      App Store
                    </p>
                  </div>
                  <span className="ml-2 text-[10px] text-text-muted bg-bg-surface-raised px-2 py-0.5 rounded-full">
                    Soon
                  </span>
                </div>

                {/* Google Play */}
                <div
                  className="flex items-center gap-3 px-5 py-3 rounded-xl border border-border-default bg-bg-surface cursor-not-allowed opacity-50 select-none"
                  title="Coming soon"
                >
                  <Play
                    className="w-5 h-5 text-success-400 shrink-0"
                    fill="currentColor"
                    strokeWidth={0}
                  />
                  <div>
                    <p className="text-[10px] text-text-muted leading-none">
                      Get it on
                    </p>
                    <p className="text-sm font-semibold text-text-primary">
                      Google Play
                    </p>
                  </div>
                  <span className="ml-2 text-[10px] text-text-muted bg-bg-surface-raised px-2 py-0.5 rounded-full">
                    Soon
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Phone mockup */}
            <motion.div
              initial={{ opacity: 0, x: 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="flex justify-center"
            >
              <div className="relative w-[230px] h-[470px] rounded-[36px] border-2 border-border-default bg-bg-base shadow-2xl overflow-hidden">
                {/* Content — mirrors the actual app's Dashboard tab */}
                <div className="flex flex-col h-full">
                  {/* App bar */}
                  <div className="flex items-center justify-between px-4 pt-5 pb-3">
                    <span className="text-[15px] font-extrabold text-text-primary tracking-tight">
                      Dashboard
                    </span>
                    <div className="flex items-center gap-2 text-text-muted">
                      <span className="text-[10px] font-medium">Sudipta</span>
                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden>
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                      </svg>
                    </div>
                  </div>

                  {/* Overview / Insights tabs */}
                  <div className="mx-4 mb-3 flex rounded-full bg-bg-surface-raised p-1 text-[10px] font-semibold">
                    <span className="flex-1 text-center py-1 rounded-full bg-primary-500 text-white">
                      Overview
                    </span>
                    <span className="flex-1 text-center py-1 text-text-muted">
                      Insights
                    </span>
                  </div>

                  {/* 2×2 stat grid */}
                  <div className="mx-4 grid grid-cols-2 gap-2">
                    <div className="p-2.5 rounded-xl bg-bg-surface border border-border-subtle">
                      <p className="text-[8px] text-text-muted mb-0.5 flex items-center gap-1">
                        <span className="text-warning-400">🔥</span> CURRENT STREAK
                      </p>
                      <p className="text-base font-bold text-text-primary leading-none">
                        23 <span className="text-[8px] font-normal text-text-muted">days</span>
                      </p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-bg-surface border border-border-subtle">
                      <p className="text-[8px] text-text-muted mb-0.5 flex items-center gap-1">
                        <CheckCircle className="w-2.5 h-2.5 text-success-400" /> TOTAL SOLVED
                      </p>
                      <p className="text-base font-bold text-text-primary leading-none">412</p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-bg-surface border border-border-subtle">
                      <p className="text-[8px] text-text-muted mb-0.5">CF RATING</p>
                      <p className="text-base font-bold leading-none" style={{ color: "#1E88E5" }}>
                        1874 <span className="text-[8px] font-normal text-text-muted">Expert</span>
                      </p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-bg-surface border border-border-subtle">
                      <p className="text-[8px] text-text-muted mb-0.5">PEAK RATING</p>
                      <p className="text-base font-bold text-text-primary leading-none">1912</p>
                    </div>
                  </div>

                  {/* Activity heatmap card */}
                  <div className="mx-4 mt-2.5 p-3 rounded-xl bg-bg-surface border border-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[9px] font-semibold text-text-primary">Activity</span>
                      <span className="text-[8px] text-text-muted">Last year</span>
                    </div>
                    <div className="grid grid-cols-7 gap-1">
                      {PHONE_HEATMAP.map((intensity, i) => (
                        <div
                          key={i}
                          className="aspect-square rounded-sm"
                          style={{ background: `rgba(99, 102, 241, ${intensity})` }}
                        />
                      ))}
                    </div>
                    <div className="flex items-center justify-end gap-1 mt-2 text-[7px] text-text-muted">
                      <span>Less</span>
                      {[0.15, 0.4, 0.65, 0.9].map((a) => (
                        <div key={a} className="w-1.5 h-1.5 rounded-[1px]" style={{ background: `rgba(99,102,241,${a})` }} />
                      ))}
                      <span>More</span>
                    </div>
                  </div>

                  {/* Bottom nav */}
                  <div className="mt-auto flex items-center justify-around border-t border-border-subtle bg-bg-surface px-2 py-2.5">
                    <div className="flex flex-col items-center gap-0.5">
                      <div className="px-3 py-1 rounded-full bg-primary-500 flex items-center justify-center">
                        <TrendingUp className="w-3 h-3 text-white" strokeWidth={2.5} />
                      </div>
                      <span className="text-[7px] text-primary-400 font-medium">Dashboard</span>
                    </div>
                    <div className="flex flex-col items-center gap-1 text-text-muted">
                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden>
                        <rect x="3" y="4" width="18" height="18" rx="2" />
                        <path d="M16 2v4M8 2v4M3 10h18" />
                      </svg>
                      <span className="text-[7px]">Contests</span>
                    </div>
                    <div className="flex flex-col items-center gap-1 text-text-muted">
                      <Users className="w-3.5 h-3.5" />
                      <span className="text-[7px]">Classes</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ──────────────────────── AI FEATURES ─────────────────────── */}
      <section
        id="ai"
        className="py-24 px-4 bg-bg-surface border-y border-border-subtle"
      >
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
            className="relative rounded-3xl overflow-hidden border border-border-subtle p-8 md:p-12"
            style={{
              background:
                "linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(6,182,212,0.06) 100%)",
            }}
          >
            {/* Decorative glow */}
            <div
              className="pointer-events-none absolute -top-16 -right-16 w-56 h-56 rounded-full opacity-25"
              style={{
                background:
                  "radial-gradient(circle, #6366F1 0%, transparent 70%)",
                filter: "blur(40px)",
              }}
              aria-hidden
            />

            <div className="relative">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/15 border border-primary-500/30 text-primary-400 text-xs font-medium mb-4">
                <Sparkles className="w-3.5 h-3.5" />
                Coming Soon
              </span>

              <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-3">
                Your Personal AI Coaching Layer
              </h2>
              <p className="text-text-secondary max-w-2xl mb-10 leading-relaxed">
                PROGNOS AI reads your entire problem-solving history and tells
                you exactly what to practice next, why you are stuck, and how to
                break through to the next rating tier.
              </p>

              <motion.div
                variants={staggerChildren}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                className="grid sm:grid-cols-3 gap-4"
              >
                {[
                  {
                    icon: Brain,
                    title: "Problem Difficulty Predictor",
                    desc: "Know before you click whether a problem is within your reach today.",
                    color: "#818CF8",
                  },
                  {
                    icon: Zap,
                    title: "Weakness-First Recommendations",
                    desc: "AI surfaces the exact tag gaps holding back your rating — no guessing needed.",
                    color: "#22D3EE",
                  },
                  {
                    icon: BarChart3,
                    title: "Personalized Practice Plans",
                    desc: "A daily training plan built from your contest history, not generic difficulty filters.",
                    color: "#34D399",
                  },
                ].map((item) => (
                  <motion.div
                    key={item.title}
                    variants={fadeUp}
                    className="p-5 rounded-2xl bg-bg-surface-raised border border-border-subtle"
                  >
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center mb-3"
                      style={{ background: item.color + "22" }}
                    >
                      <item.icon
                        className="w-4 h-4"
                        style={{ color: item.color }}
                      />
                    </div>
                    <h3 className="text-sm font-semibold text-text-primary mb-1">
                      {item.title}
                    </h3>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      {item.desc}
                    </p>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ──────────────────────── SOCIAL PROOF ────────────────────── */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Stats bar */}
          <motion.div
            variants={staggerChildren}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid grid-cols-3 gap-6 text-center mb-16"
          >
            {[
              { value: "50K+", label: "Problems tracked" },
              { value: "200+", label: "Classrooms created" },
              { value: "150+", label: "Active streaks" },
            ].map((stat) => (
              <motion.div key={stat.label} variants={fadeUp}>
                <p className="text-3xl sm:text-4xl font-extrabold text-text-primary mb-1">
                  {stat.value}
                </p>
                <p className="text-sm text-text-muted">{stat.label}</p>
              </motion.div>
            ))}
          </motion.div>

          {/* Testimonials */}
          <motion.div
            variants={staggerChildren}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid sm:grid-cols-2 gap-4"
          >
            {[
              {
                quote:
                  "Finally a tool that shows me where I am actually weak, not just how many problems I have solved. The tag analysis alone is worth it.",
                handle: "rnvyy",
                rating: 1873,
                rank: "Expert",
              },
              {
                quote:
                  "Set up a classroom for my university CP club. The leaderboard during contest week completely changed how motivated everyone is.",
                handle: "cp_instructor",
                rating: 2143,
                rank: "International Master",
              },
            ].map((t) => (
              <motion.div
                key={t.handle}
                variants={fadeUp}
                className="p-6 rounded-2xl bg-bg-surface border border-border-subtle"
              >
                <p className="text-sm text-text-secondary leading-relaxed mb-5">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-bg-surface-raised flex items-center justify-center text-sm font-bold text-text-muted shrink-0">
                    {t.handle.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <span
                      className="text-sm font-semibold"
                      style={{ color: getRatingColor(t.rating) }}
                    >
                      {t.handle}
                    </span>
                    <span className="text-xs text-text-muted ml-2">
                      &middot; {t.rank}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─────────────────── DUAL-PERSONA CTAs ────────────────────── */}
      <section className="py-24 px-4 bg-bg-surface border-y border-border-subtle">
        <div className="max-w-4xl mx-auto">
          <motion.h2
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="text-3xl font-bold text-text-primary text-center mb-12"
          >
            Who is PROGNOS for?
          </motion.h2>

          <motion.div
            variants={staggerChildren}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid sm:grid-cols-2 gap-6"
          >
            {/* Individual solver */}
            <motion.div
              variants={fadeUp}
              className="flex flex-col p-8 rounded-2xl border border-primary-500/30 bg-primary-500/5"
            >
              <div className="w-10 h-10 rounded-xl bg-primary-500/15 flex items-center justify-center mb-5">
                <TrendingUp className="w-5 h-5 text-primary-400" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-1">
                Individual Competitive Programmer
              </h3>
              <p className="text-sm text-text-muted mb-5">
                Track your own progress, understand your weaknesses, and climb
                the rating ladder with data on your side.
              </p>
              <ul className="space-y-2 mb-7 mt-1">
                {[
                  "Submission heatmap",
                  "Rating trajectory",
                  "Tag weakness analysis",
                  "Peer comparison",
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2 text-sm text-text-secondary"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-primary-400 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/login"
                className="mt-auto flex items-center justify-center w-full py-2.5 rounded-xl bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
              >
                See my dashboard
              </Link>
            </motion.div>

            {/* Classroom admin */}
            <motion.div
              variants={fadeUp}
              className="flex flex-col p-8 rounded-2xl border border-accent-500/30 bg-accent-500/5"
            >
              <div className="w-10 h-10 rounded-xl bg-accent-500/15 flex items-center justify-center mb-5">
                <Users className="w-5 h-5 text-accent-400" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-1">
                CP Classroom or Team
              </h3>
              <p className="text-sm text-text-muted mb-5">
                Run a transparent leaderboard for your students or club members
                and see exactly who needs attention.
              </p>
              <ul className="space-y-2 mb-7 mt-1">
                {[
                  "Live classroom leaderboard",
                  "Cohort analytics",
                  "Invite links",
                  "Member progress visibility",
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2 text-sm text-text-secondary"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-accent-400 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/login"
                className="mt-auto flex items-center justify-center w-full py-2.5 rounded-xl bg-primary-500 text-white text-sm font-medium hover:bg-primary-600 transition-colors"
              >
                Create a classroom
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ──────────────────────── FOOTER CTA ──────────────────────── */}
      <section className="py-24 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-3">
              Start free. No signup required.
            </h2>
            <p className="text-text-secondary mb-8">
              Enter your Codeforces handle to preview your dashboard in seconds.
            </p>
            <div className="flex justify-center">
              <HandlePreviewWidget />
            </div>
          </motion.div>
        </div>
      </section>

      {/* ───────────────────────── FOOTER ─────────────────────────── */}
      <footer className="py-8 px-4 border-t border-border-subtle bg-bg-surface">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-primary-500 flex items-center justify-center">
              <TrendingUp className="w-3 h-3 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-bold text-text-primary">PROGNOS</span>
          </div>
          <div className="flex items-center gap-6">
            <a
              href="#features"
              className="text-sm text-text-muted hover:text-text-secondary transition-colors"
            >
              Features
            </a>
            <a
              href="#classrooms"
              className="text-sm text-text-muted hover:text-text-secondary transition-colors"
            >
              Classrooms
            </a>
            <a
              href="#mobile"
              className="text-sm text-text-muted hover:text-text-secondary transition-colors"
            >
              Mobile
            </a>
            <a
              href="#ai"
              className="text-sm text-text-muted hover:text-text-secondary transition-colors"
            >
              AI
            </a>
          </div>
          <p className="text-xs text-text-muted">
            &copy; 2026 PROGNOS. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
