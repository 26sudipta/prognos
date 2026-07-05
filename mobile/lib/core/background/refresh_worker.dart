import 'dart:ui' show DartPluginRegistrant;

import 'package:dio/dio.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:workmanager/workmanager.dart';

import '../auth/auth_api.dart';
import '../config/app_config.dart';
import '../contests/contests_api.dart';
import '../db/app_database.dart';
import '../widget/home_widget_service.dart';

/// Unique names for the periodic contest-cache refresh task.
const _kRefreshTask = 'io.prognos.contest_cache_refresh';
const _kRefreshUnique = 'contest-cache-refresh';

/// Register the periodic background refresh.
///
/// M2 scope: this task **only refreshes the contest cache** — it never fires
/// notifications (that is M3). Android runs it via WorkManager on the ~8h
/// cadence below; iOS treats it as opportunistic BGAppRefresh. In both cases
/// the real freshness guarantee is the on-app-open refresh in
/// `ContestsNotifier` — the background task is a best-effort top-up.
Future<void> initBackgroundRefresh() async {
  try {
    await Workmanager().initialize(refreshCallbackDispatcher);
    await Workmanager().registerPeriodicTask(
      _kRefreshUnique,
      _kRefreshTask,
      frequency: const Duration(hours: 8),
      constraints: Constraints(networkType: NetworkType.connected),
      existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
    );
  } catch (e) {
    // Never let background scheduling break app startup.
    debugPrint('Background refresh registration failed: $e');
  }
}

/// Headless entry point. Runs in a separate isolate with no access to the
/// app's Riverpod providers, so auth + DB are reconstructed from scratch here.
@pragma('vm:entry-point')
void refreshCallbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    if (task != _kRefreshTask) return true;
    try {
      await refreshContestCacheHeadless();
      return true;
    } catch (e) {
      debugPrint('Background contest refresh failed: $e');
      // Returning false asks WorkManager to retry with backoff.
      return false;
    }
  });
}

/// Self-contained cache refresh: read the stored refresh token → rotate it for
/// an access token (persisting the rotated refresh token) → fetch the contest
/// window → replace the local cache. No-op when signed out.
Future<void> refreshContestCacheHeadless() async {
  // Background isolates must register plugins themselves.
  WidgetsFlutterBinding.ensureInitialized();
  DartPluginRegistrant.ensureInitialized();

  const storage = FlutterSecureStorage();
  final refresh = await storage.read(key: 'refresh_token');
  if (refresh == null) return; // signed out — nothing to refresh

  final base = BaseOptions(
    baseUrl: '${AppConfig.apiBaseUrl}${AppConfig.apiPrefix}',
    connectTimeout: AppConfig.connectTimeout,
    receiveTimeout: AppConfig.receiveTimeout,
    contentType: Headers.jsonContentType,
  );

  // Rotate the refresh token (old one is revoked → persist the new one, or the
  // next launch's restore breaks).
  final (access, newRefresh) =
      await AuthApi(Dio(base)).refreshMobile(refresh);
  await storage.write(key: 'refresh_token', value: newRefresh);

  final authedDio = Dio(base)
    ..options.headers['Authorization'] = 'Bearer $access';
  final fetched = await ContestsApi(authedDio).fetchContests();

  final db = AppDatabase();
  try {
    await db.replaceContests(fetched.contests);
    // Refresh the home-screen widget with the new next-contest (R7). The
    // headless isolate already registered plugins above, so the channel works.
    await updateHomeWidget(db);
  } finally {
    await db.close();
  }
}
