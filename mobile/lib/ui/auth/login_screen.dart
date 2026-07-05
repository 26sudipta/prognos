import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/auth_controller.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_theme.dart';
import '../widgets/app_logo.dart';

/// Sign-in screen. Single "Continue with Google" action — the only auth method
/// (matches the web). Shows a spinner while the flow runs and an inline error
/// if it fails (cancellation is silent).
class LoginScreen extends ConsumerWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final busy = auth.isLoading;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),
              // Wordmark — shared logo, matches the web favicon.
              const AppLogo(size: 64),
              const SizedBox(height: 20),
              Text('PROGNOS',
                  style: AppTheme.mono(
                      fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
              const SizedBox(height: 8),
              const Text(
                'Your competitive programming, tracked.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textSecondary),
              ),
              const Spacer(),
              if (auth.hasError)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    'Sign-in failed. Please try again.',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: AppColors.danger400, fontSize: 13),
                  ),
                ),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: busy ? null : () => ref.read(authControllerProvider.notifier).signIn(),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary600,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppTheme.radius),
                    ),
                  ),
                  icon: busy
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.login_rounded, size: 20),
                  label: Text(busy ? 'Signing in…' : 'Continue with Google'),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
