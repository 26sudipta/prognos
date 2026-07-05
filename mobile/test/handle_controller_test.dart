import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prognos/core/handles/handle_models.dart';
import 'package:prognos/core/handles/handles_providers.dart';

import 'support/handle_fakes.dart';

ProviderContainer _c(FakeHandlesApi api) {
  final c = ProviderContainer(
    overrides: [handlesApiProvider.overrideWithValue(api)],
  );
  addTearDown(c.dispose);
  return c;
}

void main() {
  test('no handle → HandleNone', () async {
    final c = _c(FakeHandlesApi());
    expect(await c.read(handleControllerProvider.future), isA<HandleNone>());
  });

  test('verified handle → HandleVerified', () async {
    final c = _c(FakeHandlesApi(handles: [verifiedHandle()]));
    final s = await c.read(handleControllerProvider.future);
    expect(s, isA<HandleVerified>());
    expect((s as HandleVerified).handle, 'tourist');
  });

  test('pending token restores to HandlePending', () async {
    final c = _c(FakeHandlesApi(handles: [pendingHandle()]));
    final s = await c.read(handleControllerProvider.future);
    expect(s, isA<HandlePending>());
    expect((s as HandlePending).token, 'PGS-ABC123');
  });

  test('locked handle → HandleLocked', () async {
    final c = _c(FakeHandlesApi(handles: [lockedHandle()]));
    expect(await c.read(handleControllerProvider.future), isA<HandleLocked>());
  });

  test('initiate moves to pending', () async {
    final c = _c(FakeHandlesApi());
    await c.read(handleControllerProvider.future);
    await c.read(handleControllerProvider.notifier).initiate('tourist');
    final s = c.read(handleControllerProvider).value;
    expect(s, isA<HandlePending>());
    expect((s as HandlePending).handle, 'tourist');
  });

  test('confirm success → HandleVerified', () async {
    final c = _c(FakeHandlesApi(handles: [pendingHandle()]));
    await c.read(handleControllerProvider.future);
    await c.read(handleControllerProvider.notifier).confirm();
    expect(c.read(handleControllerProvider).value, isA<HandleVerified>());
  });

  test('confirm mismatch keeps pending with attempts remaining', () async {
    final api = FakeHandlesApi(
      handles: [pendingHandle()],
      confirmError:
          const ConfirmException(ConfirmFailure.mismatch, attemptsRemaining: 2),
    );
    final c = _c(api);
    await c.read(handleControllerProvider.future);
    await c.read(handleControllerProvider.notifier).confirm();
    final s = c.read(handleControllerProvider).value;
    expect(s, isA<HandlePending>());
    expect((s as HandlePending).attemptsRemaining, 2);
  });

  test('confirm lockout re-derives to HandleLocked', () async {
    final api = FakeHandlesApi(
      handles: [pendingHandle()],
      confirmError: const ConfirmException(ConfirmFailure.locked),
    );
    final c = _c(api);
    await c.read(handleControllerProvider.future);
    // Server now reports the handle as locked.
    api.handles = [lockedHandle()];
    await c.read(handleControllerProvider.notifier).confirm();
    expect(c.read(handleControllerProvider).value, isA<HandleLocked>());
  });
}
