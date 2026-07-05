import 'package:flutter/material.dart';

import 'theme/app_theme.dart';
import 'ui/auth/auth_gate.dart';

/// Root application widget. Dark-first, no debug banner, single home shell.
/// Routing (deep links for `prognos://join/{token}` and contest notifications)
/// is added in M3/M5.
class PrognosApp extends StatelessWidget {
  const PrognosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PROGNOS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      themeMode: ThemeMode.dark,
      home: const AuthGate(),
    );
  }
}
