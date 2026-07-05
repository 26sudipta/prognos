/// Deterministic notification IDs for reminders.
///
/// Two hard constraints drove this:
///  1. **Cross-isolate / cross-restart determinism.** Reconcile may run from
///     different isolates and app launches; the same (contest, lead) must always
///     map to the same ID so we schedule/cancel idempotently. Dart's
///     `String.hashCode` / `Object.hash` are *not* guaranteed stable across
///     isolates or releases, so we use a fixed FNV-1a over `"contestId:leadMin"`.
///  2. **Android's 32-bit ID ceiling.** Notification IDs are Java `int`; a value
///     above 2³¹−1 misbehaves. We mask to 31 bits.
int reminderNotifId(String contestId, int leadMinutes) =>
    _fnv1a32('$contestId:$leadMinutes') & 0x7FFFFFFF;

/// FNV-1a, 32-bit. Runs on the native VM (64-bit ints), masking each step to
/// 32 bits so the result is identical everywhere.
int _fnv1a32(String s) {
  var hash = 0x811c9dc5;
  for (final unit in s.codeUnits) {
    hash ^= unit;
    hash = (hash * 0x01000193) & 0xFFFFFFFF;
  }
  return hash;
}
