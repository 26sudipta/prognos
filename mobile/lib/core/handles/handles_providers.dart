import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../analytics/analytics_providers.dart';
import '../network/dio_client.dart';
import 'handle_models.dart';
import 'handles_api.dart';

final handlesApiProvider = Provider<HandlesApi>(
  (ref) => HandlesApi(ref.watch(dioProvider)),
);

// ─── State machine ──────────────────────────────────────────────────────────

sealed class HandleState {
  const HandleState();
}

/// No handle (or a re-initiate is needed). [message] surfaces the reason.
class HandleNone extends HandleState {
  const HandleNone([this.message]);
  final String? message;
}

/// A token has been issued; awaiting the user to paste it + confirm.
/// [attemptsRemaining]/[error] are set after a failed confirm.
class HandlePending extends HandleState {
  const HandlePending({
    required this.handleId,
    required this.handle,
    required this.token,
    required this.expiresAt,
    this.attemptsRemaining,
    this.error,
  });
  final String handleId;
  final String handle;
  final String token;
  final DateTime expiresAt;
  final int? attemptsRemaining;
  final String? error;
}

class HandleLocked extends HandleState {
  const HandleLocked({required this.handle, this.lockoutExpiresAt});
  final String handle;
  final DateTime? lockoutExpiresAt;
}

class HandleVerified extends HandleState {
  const HandleVerified(this.handle);
  final String handle;
}

// ─── Controller ─────────────────────────────────────────────────────────────

class HandleController extends AsyncNotifier<HandleState> {
  HandlesApi get _api => ref.read(handlesApiProvider);

  @override
  Future<HandleState> build() async => _derive(await _api.list());

  HandleState _derive(List<Handle> handles) {
    if (handles.isEmpty) return const HandleNone();
    final h = handles.first;
    if (h.isVerified) return HandleVerified(h.handle);
    if (h.isLocked &&
        h.lockoutExpiresAt != null &&
        h.lockoutExpiresAt!.isAfter(DateTime.now().toUtc())) {
      return HandleLocked(handle: h.handle, lockoutExpiresAt: h.lockoutExpiresAt);
    }
    if (h.verificationToken != null) {
      return HandlePending(
        handleId: h.id,
        handle: h.handle,
        token: h.verificationToken!,
        expiresAt: h.verificationTokenExpiresAt ?? DateTime.now().toUtc(),
      );
    }
    return const HandleNone();
  }

  Future<void> initiate(String handle) async {
    state = const AsyncLoading();
    try {
      final init = await _api.initiate(handle.trim());
      state = AsyncData(HandlePending(
        handleId: init.handleId,
        handle: init.handle,
        token: init.token,
        expiresAt: init.expiresAt,
      ));
    } on DioException catch (e) {
      state = AsyncData(HandleNone(_detailMessage(e) ?? 'Could not start verification.'));
    }
  }

  Future<void> confirm() async {
    final cur = state.value;
    if (cur is! HandlePending) return;
    state = const AsyncLoading();
    try {
      await _api.confirm(cur.handleId);
      // Success → dashboard should re-fetch (has_verified_handle flips).
      ref.invalidate(analyticsProvider);
      state = AsyncData(HandleVerified(cur.handle));
    } on ConfirmException catch (e) {
      switch (e.kind) {
        case ConfirmFailure.mismatch:
          if ((e.attemptsRemaining ?? 1) <= 0) {
            state = AsyncData(_derive(await _api.list())); // now locked
          } else {
            state = AsyncData(HandlePending(
              handleId: cur.handleId,
              handle: cur.handle,
              token: cur.token,
              expiresAt: cur.expiresAt,
              attemptsRemaining: e.attemptsRemaining,
              error: 'Token not found in your profile yet.',
            ));
          }
        case ConfirmFailure.locked:
          state = AsyncData(_derive(await _api.list()));
        case ConfirmFailure.expired:
          state = const AsyncData(
              HandleNone('Token expired — enter your handle again.'));
        case ConfirmFailure.notFound:
        case ConfirmFailure.unknown:
          state = const AsyncData(
              HandleNone('Verification failed — please try again.'));
      }
    }
  }

  Future<void> unlink() async {
    final cur = state.value;
    final id = switch (cur) {
      HandlePending(:final handleId) => handleId,
      _ => null,
    };
    if (id != null) {
      try {
        await _api.unlink(id);
      } catch (_) {}
    }
    ref.invalidate(analyticsProvider);
    state = const AsyncData(HandleNone());
  }

  String? _detailMessage(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['detail'] is String) return data['detail'] as String;
    return null;
  }
}

final handleControllerProvider =
    AsyncNotifierProvider<HandleController, HandleState>(HandleController.new);
