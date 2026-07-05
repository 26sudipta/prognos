import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/background/refresh_worker.dart';

/// Entry point. Kept deliberately minimal for cold-start speed (mobile plan
/// §6): the first frame does only what's needed to render. Heavy init
/// (timezone db, sync, widget updates) is deferred to post-first-frame in the
/// slices that introduce it.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: PrognosApp()));

  // Deferred, off the critical path: schedule the periodic contest-cache
  // refresh once the first frame is on screen (M2). Best-effort — failure here
  // never affects the running app.
  WidgetsBinding.instance.addPostFrameCallback((_) {
    initBackgroundRefresh();
  });
}
