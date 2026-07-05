import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/auth_controller.dart';
import '../../theme/app_colors.dart';
import '../widgets/app_logo.dart';
import '../shell/home_shell.dart';
import 'login_screen.dart';

/// Routes between the login screen and the app shell based on auth state.
/// While the launch session-restore runs, shows a minimal splash (no spinner
/// flash for a returning user — restore is usually fast).
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);

    return auth.when(
      loading: () => const _Splash(),
      // On restore error we still fall back to login (never a dead-end).
      error: (_, _) => const LoginScreen(),
      data: (user) => user == null ? const LoginScreen() : const HomeShell(),
    );
  }
}

class _Splash extends StatelessWidget {
  const _Splash();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.bgBase,
      body: Center(child: AnimatedAppLogo(size: 72)),
    );
  }
}
