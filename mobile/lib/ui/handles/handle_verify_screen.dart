import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/handles/handles_providers.dart';
import '../../theme/app_colors.dart';

/// Codeforces handle verification wizard (M5). Enter handle → copy the
/// `PGS-XXXX` token into your CF Organization field → verify. Mirrors the web
/// wizard; state is driven by [handleControllerProvider] and restores across
/// reopen from `GET /handles`.
class HandleVerifyScreen extends ConsumerWidget {
  const HandleVerifyScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(handleControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Verify Codeforces handle')),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (state) => switch (state) {
          HandleNone() => _EnterHandle(message: state.message),
          HandlePending() => _Pending(state: state),
          HandleLocked() => _Locked(state: state),
          HandleVerified() => _Verified(handle: state.handle),
        },
      ),
    );
  }
}

class _EnterHandle extends ConsumerStatefulWidget {
  const _EnterHandle({this.message});
  final String? message;
  @override
  ConsumerState<_EnterHandle> createState() => _EnterHandleState();
}

class _EnterHandleState extends ConsumerState<_EnterHandle> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text(
          'Link your Codeforces handle',
          style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        const Text(
          'We verify ownership by asking you to place a one-time token in your '
          'Codeforces profile. This unlocks your dashboard and lets you join '
          'classrooms.',
          style: TextStyle(
              color: AppColors.textSecondary, fontSize: 13.5, height: 1.4),
        ),
        if (widget.message != null) ...[
          const SizedBox(height: 14),
          _Banner(widget.message!, color: AppColors.warning400),
        ],
        const SizedBox(height: 20),
        TextField(
          controller: _controller,
          autocorrect: false,
          textInputAction: TextInputAction.done,
          style: const TextStyle(color: AppColors.textPrimary),
          decoration: const InputDecoration(
            labelText: 'Codeforces handle',
            hintText: 'tourist',
          ),
          onSubmitted: (_) => _submit(),
        ),
        const SizedBox(height: 16),
        FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: AppColors.primary500,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          onPressed: _submit,
          child: const Text('Get verification token',
              style: TextStyle(fontWeight: FontWeight.w700)),
        ),
      ],
    );
  }

  void _submit() {
    final handle = _controller.text.trim();
    if (handle.isEmpty) return;
    ref.read(handleControllerProvider.notifier).initiate(handle);
  }
}

class _Pending extends ConsumerWidget {
  const _Pending({required this.state});
  final HandlePending state;

  Future<void> _openCf() async {
    final uri = Uri.parse('https://codeforces.com/settings/social');
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _Step(
          n: 1,
          title: 'Copy your token',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GestureDetector(
                onTap: () {
                  Clipboard.setData(ClipboardData(text: state.token));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Token copied')),
                  );
                },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.bgSurfaceRaised,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.borderDefault),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        state.token,
                        style: const TextStyle(
                          color: AppColors.primary400,
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 2,
                          fontFamily: 'monospace',
                        ),
                      ),
                      const Icon(Icons.copy_rounded,
                          size: 18, color: AppColors.textMuted),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        _Step(
          n: 2,
          title: 'Paste it into Codeforces',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Open your Codeforces social settings and paste the token into '
                'the "Organization" field, then Save.',
                style: TextStyle(
                    color: AppColors.textSecondary, fontSize: 13, height: 1.4),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: _openCf,
                icon: const Icon(Icons.open_in_new_rounded, size: 16),
                label: const Text('Open Codeforces settings'),
              ),
            ],
          ),
        ),
        _Step(
          n: 3,
          title: 'Verify',
          last: true,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (state.error != null) ...[
                _Banner(
                  '${state.error!}'
                  '${state.attemptsRemaining != null ? ' (${state.attemptsRemaining} attempts left)' : ''}',
                  color: AppColors.danger400,
                ),
                const SizedBox(height: 12),
              ],
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary500,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  minimumSize: const Size(double.infinity, 0),
                ),
                onPressed: () =>
                    ref.read(handleControllerProvider.notifier).confirm(),
                child: const Text('I\'ve added it — Verify',
                    style: TextStyle(fontWeight: FontWeight.w700)),
              ),
              const SizedBox(height: 8),
              Center(
                child: TextButton(
                  onPressed: () =>
                      ref.read(handleControllerProvider.notifier).unlink(),
                  child: const Text('Start over',
                      style: TextStyle(color: AppColors.textMuted)),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Locked extends StatelessWidget {
  const _Locked({required this.state});
  final HandleLocked state;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lock_clock_rounded,
                size: 48, color: AppColors.warning400),
            const SizedBox(height: 16),
            const Text('Temporarily locked',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            const Text(
              'Too many failed attempts. Please try again later.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13.5),
            ),
          ],
        ),
      ),
    );
  }
}

class _Verified extends StatelessWidget {
  const _Verified({required this.handle});
  final String handle;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.verified_rounded,
                size: 56, color: AppColors.success400),
            const SizedBox(height: 16),
            Text('$handle verified.',
                style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 19,
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            const Text(
              'Your dashboard is syncing now — analytics will appear shortly.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13.5),
            ),
            const SizedBox(height: 24),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primary500,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 13),
              ),
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Go to Dashboard',
                  style: TextStyle(fontWeight: FontWeight.w700)),
            ),
          ],
        ),
      ),
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({
    required this.n,
    required this.title,
    required this.child,
    this.last = false,
  });
  final int n;
  final String title;
  final Widget child;
  final bool last;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: last ? 0 : 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 24,
                height: 24,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                    color: AppColors.primary500, shape: BoxShape.circle),
                child: Text('$n',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 10),
              Text(title,
                  style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 15,
                      fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 12),
          Padding(padding: const EdgeInsets.only(left: 34), child: child),
        ],
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner(this.text, {required this.color});
  final String text;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(text,
            style: TextStyle(color: color, fontSize: 12.5, height: 1.35)),
      );
}
