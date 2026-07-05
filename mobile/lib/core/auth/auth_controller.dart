import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../analytics/analytics_providers.dart';
import '../classrooms/classrooms_providers.dart';
import '../contests/contests_providers.dart';
import '../handles/handles_providers.dart';
import '../reminders/reminders_providers.dart';
import 'app_user.dart';
import 'auth_repository.dart';

/// App-wide auth state. `build()` attempts a silent session restore on launch,
/// so the UI shows a splash while `loading`, the login screen when `data == null`,
/// and the app shell when `data` is a user.
class AuthController extends AsyncNotifier<AppUser?> {
  @override
  Future<AppUser?> build() {
    return ref.read(authRepositoryProvider).restoreSession();
  }

  Future<void> signIn() async {
    state = const AsyncLoading();
    try {
      final user = await ref.read(authRepositoryProvider).signInWithGoogle();
      state = AsyncData(user); // null → user canceled; gate stays on login
    } catch (e, st) {
      if (kDebugMode) debugPrint('Sign-in failed: $e');
      state = AsyncError(e, st);
    }
  }

  Future<void> signOut() async {
    await ref.read(authRepositoryProvider).signOut();
    // Wipe user-scoped local state so the next account on this device never
    // sees the previous user's private analytics, or inherits their reminders.
    await ref.read(reminderSchedulerProvider).cancelAll();
    await ref.read(appDatabaseProvider).clearUserData();
    // Invalidate EVERY per-user, non-autoDispose provider — clearing drift is
    // necessary but not sufficient, since these hold the previous user's data in
    // memory across a logout/login on the same device. Add new ones here.
    ref.invalidate(analyticsProvider);
    ref.invalidate(remindersControllerProvider);
    ref.invalidate(classroomsListProvider);
    ref.invalidate(handleControllerProvider);
    state = const AsyncData(null);
  }
}

final authControllerProvider =
    AsyncNotifierProvider<AuthController, AppUser?>(AuthController.new);
