import 'dart:convert';

import 'package:home_widget/home_widget.dart';

import '../contests/contest_format.dart';
import '../db/app_database.dart';

/// Fully-qualified Android widget provider class (matches the Kotlin class).
const _kAndroidProvider = 'io.prognos.prognos.ContestWidgetProvider';

/// Flat key/value payload the native widget renders. A home-screen widget can
/// only display **pre-computed** values (RemoteViews reads SharedPreferences via
/// home_widget) — it cannot read drift or tick a per-second countdown. So we
/// compute a *static* relative string here and recompute it on every update
/// (app open, cache refresh, the 6h workmanager cycle).
Future<Map<String, String>> buildWidgetPayload(
  AppDatabase db, {
  DateTime? nowUtc,
}) async {
  final now = nowUtc ?? DateTime.now().toUtc();

  // Next / live contest from the cached window.
  final contests = await db.allContests();
  final next = nextContest(contests, now);

  final String title;
  final String subtitle;
  if (next == null) {
    title = 'No upcoming contests';
    subtitle = '';
  } else {
    title = next.name;
    final rel = isLive(next, now) ? 'LIVE' : _relativeStart(next.startTime, now);
    subtitle = '${platformDisplayName(next.platform)} · $rel';
  }

  // Current streak from the cached dashboard (absent until a verified-handle
  // fetch has run → render "—", never crash).
  var streak = '—';
  final dashRaw = await db.readSetting('analytics.dashboard');
  if (dashRaw != null) {
    try {
      final m = jsonDecode(dashRaw) as Map<String, dynamic>;
      streak = (m['current_streak'] as num?)?.toInt().toString() ?? '—';
    } catch (_) {/* keep — */}
  }

  return {
    'next_title': title,
    'next_subtitle': subtitle,
    'streak': streak,
  };
}

/// Static "time until start" — no ticking (widgets refresh at most ~30 min).
String _relativeStart(DateTime startUtc, DateTime nowUtc) {
  final d = startUtc.difference(nowUtc);
  if (d.inMinutes < 1) return 'starting now';
  if (d.inHours < 1) return 'in ${d.inMinutes}m';
  if (d.inHours < 24) return 'in ${d.inHours}h ${d.inMinutes % 60}m';
  return 'in ${d.inDays}d';
}

/// Push the current payload to the home-screen widget. Safe to call from the
/// main isolate or the workmanager isolate; failures never propagate.
Future<void> updateHomeWidget(AppDatabase db) async {
  try {
    final payload = await buildWidgetPayload(db);
    for (final e in payload.entries) {
      await HomeWidget.saveWidgetData<String>(e.key, e.value);
    }
    await HomeWidget.updateWidget(qualifiedAndroidName: _kAndroidProvider);
  } catch (_) {
    // No widget placed / platform unavailable — nothing to do.
  }
}
