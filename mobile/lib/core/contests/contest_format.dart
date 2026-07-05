import 'package:flutter/painting.dart';
import 'package:intl/intl.dart';

import '../db/app_database.dart';

/// Presentation helpers ported from the web `frontend/app/_lib/contests.ts`
/// so mobile groups, colours, and formats contests **identically** to the web.
///
/// Golden rule: every contest instant is stored UTC; convert to **local** with
/// `.toLocal()` before grouping or formatting. Grouping in UTC would silently
/// put a contest on the wrong calendar day for users far from GMT.

// ─── Platform identity ──────────────────────────────────────────────────────

const _platformColors = <String, int>{
  'codeforces.com': 0xFF1A81C4,
  'atcoder.jp': 0xFF9B7EC8,
  'leetcode.com': 0xFFFFA116,
  'codechef.com': 0xFFF0923B,
  'hackerrank.com': 0xFF00EA64,
  'hackerearth.com': 0xFF44C4A1,
  'topcoder.com': 0xFFEF3A3A,
  'codingcompetitions.withgoogle.com': 0xFF4285F4,
};

const _platformAbbr = <String, String>{
  'codeforces.com': 'CF',
  'atcoder.jp': 'AC',
  'leetcode.com': 'LC',
  'codechef.com': 'CC',
  'hackerrank.com': 'HR',
  'hackerearth.com': 'HE',
  'topcoder.com': 'TC',
  'codingcompetitions.withgoogle.com': 'GC',
};

const _platformDisplay = <String, String>{
  'codeforces.com': 'Codeforces',
  'atcoder.jp': 'AtCoder',
  'leetcode.com': 'LeetCode',
  'codechef.com': 'CodeChef',
  'hackerrank.com': 'HackerRank',
  'hackerearth.com': 'HackerEarth',
  'topcoder.com': 'Topcoder',
  'codingcompetitions.withgoogle.com': 'Google',
};

Color platformColor(String platform) =>
    Color(_platformColors[platform.toLowerCase()] ?? 0xFF64748B);

String platformAbbr(String platform) {
  final p = platform.toLowerCase();
  return _platformAbbr[p] ??
      (platform.length >= 2
          ? platform.substring(0, 2).toUpperCase()
          : platform.toUpperCase());
}

String platformDisplayName(String platform) =>
    _platformDisplay[platform.toLowerCase()] ?? platform;

// ─── Time / date formatting (all local TZ) ──────────────────────────────────

String formatLocalTimeOnly(DateTime utc) => DateFormat.Hm().format(utc.toLocal());

// "Jun 28 · 17:35"
String formatLocalDateShort(DateTime utc) {
  final l = utc.toLocal();
  return '${DateFormat('MMM d').format(l)} · ${DateFormat.Hm().format(l)}';
}

// "Sat, Jul 12 · 17:35"
String formatLocalDateTimeShort(DateTime utc) {
  final l = utc.toLocal();
  return '${DateFormat('EEE, MMM d').format(l)} · ${DateFormat.Hm().format(l)}';
}

// "Saturday, July 12 at 17:35"
String formatLocalDateTimeLong(DateTime utc) {
  final l = utc.toLocal();
  return '${DateFormat('EEEE, MMMM d').format(l)} at ${DateFormat.Hm().format(l)}';
}

// "Saturday, July 12" — list group headers, from a local DateTime
String formatDateHeader(DateTime local) =>
    DateFormat('EEEE, MMMM d').format(local);

// "45m", "2h", "2h 15m" — and days for very long events ("40d") so the label
// stays compact (some "contests" span weeks and would overflow as hours).
String formatDuration(int seconds) {
  final h = seconds ~/ 3600;
  final m = (seconds % 3600) ~/ 60;
  if (h >= 48) {
    final d = h ~/ 24;
    final rh = h % 24;
    return rh == 0 ? '${d}d' : '${d}d ${rh}h';
  }
  if (h == 0) return '${m}m';
  if (m == 0) return '${h}h';
  return '${h}h ${m}m';
}

// End-time label; includes the date only when the contest crosses local midnight.
String formatLocalEndLabel(DateTime startUtc, DateTime endUtc) {
  final s = startUtc.toLocal();
  final e = endUtc.toLocal();
  final sameDay = s.year == e.year && s.month == e.month && s.day == e.day;
  return sameDay ? formatLocalTimeOnly(endUtc) : formatLocalDateTimeShort(endUtc);
}

// ─── Live / next helpers ────────────────────────────────────────────────────

bool isLive(Contest c, [DateTime? nowUtc]) {
  final now = (nowUtc ?? DateTime.now().toUtc());
  return !now.isBefore(c.startTime) && now.isBefore(c.endTime);
}

/// The contest to feature: the live one, else the soonest upcoming, else null.
Contest? nextContest(List<Contest> contests, [DateTime? nowUtc]) {
  final now = nowUtc ?? DateTime.now().toUtc();
  Contest? live;
  Contest? upcoming;
  for (final c in contests) {
    if (isLive(c, now)) {
      if (live == null || c.startTime.isBefore(live.startTime)) live = c;
    } else if (c.startTime.isAfter(now)) {
      if (upcoming == null || c.startTime.isBefore(upcoming.startTime)) {
        upcoming = c;
      }
    }
  }
  return live ?? upcoming;
}

// ─── Urgency swim-lane grouping (list view) ─────────────────────────────────

enum UrgencyLane { live, today, thisWeek, nextWeek, later }

extension UrgencyLaneLabel on UrgencyLane {
  String get label => switch (this) {
        UrgencyLane.live => 'Live Now',
        UrgencyLane.today => 'Today',
        UrgencyLane.thisWeek => 'This Week',
        UrgencyLane.nextWeek => 'Next Week',
        UrgencyLane.later => 'Later',
      };
}

class ContestLane {
  const ContestLane(this.lane, this.contests);
  final UrgencyLane lane;
  final List<Contest> contests;
}

DateTime _localMidnight(DateTime local) =>
    DateTime(local.year, local.month, local.day);

/// Monday 00:00 (local) of the week containing [local]. Mirrors the web's
/// Mon-anchored week (Dart weekday: Mon=1…Sun=7).
DateTime mondayOf(DateTime local) {
  final midnight = _localMidnight(local);
  return midnight.subtract(Duration(days: midnight.weekday - 1));
}

/// Group into urgency lanes exactly like the web Direction-B list.
/// Ended contests are omitted. Lanes are returned in fixed order, empty ones
/// dropped, each lane sorted by start time ascending.
List<ContestLane> groupByUrgency(List<Contest> contests, [DateTime? nowUtc]) {
  final nowU = nowUtc ?? DateTime.now().toUtc();
  final nowLocal = nowU.toLocal();
  final todayMidnight = _localMidnight(nowLocal);
  final monday = mondayOf(nowLocal);
  final sundayEnd = monday.add(const Duration(days: 7)); // exclusive end of week
  final nextSundayEnd = monday.add(const Duration(days: 14));

  final buckets = <UrgencyLane, List<Contest>>{
    for (final l in UrgencyLane.values) l: <Contest>[],
  };

  for (final c in contests) {
    if (isLive(c, nowU)) {
      buckets[UrgencyLane.live]!.add(c);
    } else if (c.startTime.isAfter(nowU)) {
      final startLocal = c.startTime.toLocal();
      final startDay = _localMidnight(startLocal);
      if (startDay == todayMidnight) {
        buckets[UrgencyLane.today]!.add(c);
      } else if (startLocal.isBefore(sundayEnd)) {
        buckets[UrgencyLane.thisWeek]!.add(c);
      } else if (startLocal.isBefore(nextSundayEnd)) {
        buckets[UrgencyLane.nextWeek]!.add(c);
      } else {
        buckets[UrgencyLane.later]!.add(c);
      }
    }
    // ended contests omitted
  }

  final lanes = <ContestLane>[];
  for (final l in UrgencyLane.values) {
    final list = buckets[l]!;
    if (list.isEmpty) continue;
    list.sort((a, b) => a.startTime.compareTo(b.startTime));
    lanes.add(ContestLane(l, list));
  }
  return lanes;
}

// ─── Calendar week helpers (calendar view) ──────────────────────────────────

/// 7 local midnights, Mon–Sun, for the week at [weekOffset] (0 = current).
List<DateTime> localWeekDays(int weekOffset) {
  final monday = mondayOf(DateTime.now())
      .add(Duration(days: weekOffset * 7));
  return List.generate(7, (i) => monday.add(Duration(days: i)));
}

/// Contests whose **local** start date falls on [localDay] (00:00 local).
List<Contest> contestsOnLocalDay(List<Contest> contests, DateTime localDay) {
  final next = localDay.add(const Duration(days: 1));
  final result = contests.where((c) {
    final s = c.startTime.toLocal();
    return !s.isBefore(localDay) && s.isBefore(next);
  }).toList();
  result.sort((a, b) => a.startTime.compareTo(b.startTime));
  return result;
}

// ─── Distinct platforms (for filter chips, derived from cache) ──────────────

List<String> distinctPlatforms(List<Contest> contests) {
  final set = <String>{for (final c in contests) c.platform};
  final list = set.toList()..sort();
  return list;
}
