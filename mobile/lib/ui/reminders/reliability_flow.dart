import 'dart:io' show Platform;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../core/reminders/oem_settings.dart';
import '../../core/reminders/reminders_providers.dart';
import '../../theme/app_colors.dart';

/// First-run reminder opt-in. Kept deliberately simple for non-technical users:
/// two one-tap system dialogs (notifications + background activity), then an
/// **honest** test — a real alarm scheduled ~15s out. The user confirms whether
/// it actually arrived; if not, one tap opens the right settings and they retry.
/// Returns true once the user confirms reminders work.
Future<bool> runReminderReliabilityFlow(
  BuildContext context,
  WidgetRef ref,
) async {
  final result = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.bgSurface,
    showDragHandle: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => const _ReliabilitySheet(),
  );
  if (result == true) {
    await ref.read(remindersRepositoryProvider).markOnboarded();
  }
  return result ?? false;
}

enum _Phase { intro, verify }

class _ReliabilitySheet extends ConsumerStatefulWidget {
  const _ReliabilitySheet();

  @override
  ConsumerState<_ReliabilitySheet> createState() => _ReliabilitySheetState();
}

class _ReliabilitySheetState extends ConsumerState<_ReliabilitySheet> {
  _Phase _phase = _Phase.intro;
  bool _busy = false;
  String? _fixTip; // shown after "didn't get it"

  /// One-tap grants → schedule the honest test → ask the user if it arrived.
  Future<void> _enable() async {
    setState(() => _busy = true);
    final scheduler = ref.read(reminderSchedulerProvider);

    // 1. Notifications (one-tap system dialog).
    await scheduler.requestNotificationsPermission();
    // 2. Background activity (one-tap system dialog). Best-effort.
    if (Platform.isAndroid) {
      final status = await Permission.ignoreBatteryOptimizations.status;
      if (!status.isGranted) {
        await Permission.ignoreBatteryOptimizations.request();
      }
    }
    // 3. Honest test through the real alarm path.
    await scheduler.scheduleTest();

    if (!mounted) return;
    setState(() {
      _busy = false;
      _phase = _Phase.verify;
    });
  }

  Future<void> _testAgain() async {
    setState(() => _busy = true);
    await ref.read(reminderSchedulerProvider).scheduleTest();
    if (mounted) setState(() => _busy = false);
  }

  /// The one thing that keeps reminders alive on aggressive OEMs: stop the OS
  /// from putting PROGNOS to sleep / force-stopping it (which cancels every
  /// alarm). Deep-links **straight to the phone's own** Auto-start / battery
  /// screen so the user just flips a switch, then shows the matching one-liner.
  Future<void> _openKeepAlive() async {
    final vendor = await OemSettings.openAutoStart();
    if (mounted) setState(() => _fixTip = _keepAliveTip(vendor));
  }

  /// Instruction for the screen [OemSettings.openAutoStart] just opened, keyed by
  /// the vendor it reported.
  String _keepAliveTip(String vendor) {
    switch (vendor) {
      case 'samsung':
        return 'Here: tap "App power management" (a.k.a. Background usage limits) '
            '→ "Never sleeping apps" → Add → pick PROGNOS. That stops Samsung '
            'force-stopping it (which cancels alarms). Then come back and tap Test again.';
      case 'xiaomi':
        return 'Turn ON Autostart for PROGNOS here, and set its Battery saver to '
            '"No restrictions". Then come back and tap Test again.';
      case 'oppo':
        return 'Turn ON "Allow auto-launch" and background activity for PROGNOS. '
            'Then come back and tap Test again.';
      case 'oneplus':
        return 'Enable auto-launch for PROGNOS (and set battery to "Don\'t '
            'optimize"). Then come back and tap Test again.';
      case 'vivo':
        return 'Turn ON auto-start / background activity for PROGNOS. Then come '
            'back and tap Test again.';
      case 'huawei':
        return 'Set PROGNOS to "Manage manually" and enable auto-launch, secondary '
            'launch and run-in-background. Then come back and tap Test again.';
      case 'asus':
        return 'Add PROGNOS to the Auto-start Manager allow list. Then come back '
            'and tap Test again.';
      default: // 'other' / 'app_details'
        return 'Allow PROGNOS unrestricted background/battery use, and turn off any '
            '"put app to sleep" option here. Then come back and tap Test again.';
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _phase == _Phase.verify
                      ? Icons.hourglass_top_rounded
                      : Icons.notifications_active_rounded,
                  color: AppColors.primary400,
                ),
                const SizedBox(width: 10),
                Text(
                  _phase == _Phase.verify
                      ? 'Did the test alert arrive?'
                      : 'Turn on contest reminders',
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (_phase == _Phase.intro) ..._intro() else ..._verify(),
          ],
        ),
      ),
    );
  }

  List<Widget> _intro() => [
        const Text(
          'Get a heads-up before every contest starts — even when your phone is '
          'locked. Just tap Enable and allow the two prompts.',
          style: TextStyle(
              color: AppColors.textSecondary, fontSize: 14, height: 1.45),
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary500,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onPressed: _busy ? null : _enable,
            child: Text(_busy ? 'Setting up…' : 'Enable reminders',
                style: const TextStyle(fontWeight: FontWeight.w700)),
          ),
        ),
        Center(
          child: TextButton(
            onPressed: _busy ? null : () => Navigator.of(context).pop(false),
            child: const Text('Not now',
                style: TextStyle(color: AppColors.textMuted)),
          ),
        ),
      ];

  List<Widget> _verify() => [
        const Text(
          'We just sent a test alert — it should ring in about 15 seconds '
          '(you can lock your phone). Did you get it?\n\n'
          'It rings even in Do Not Disturb. On Samsung, Xiaomi, Oppo, Vivo and '
          'similar phones, tap "Keep it working" and flip the one switch so the '
          'system never stops your reminders.',
          style: TextStyle(
              color: AppColors.textSecondary, fontSize: 14, height: 1.45),
        ),
        if (_fixTip != null) ...[
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.warning500.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              _fixTip!,
              style: const TextStyle(
                  color: AppColors.warning400, fontSize: 13, height: 1.4),
            ),
          ),
        ],
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.success500,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onPressed: _busy ? null : () => Navigator.of(context).pop(true),
            icon: const Icon(Icons.check_rounded, size: 20),
            label: const Text("Yes — I'm all set",
                style: TextStyle(fontWeight: FontWeight.w700)),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            if (Platform.isAndroid) ...[
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _busy ? null : _openKeepAlive,
                  icon: const Icon(Icons.shield_moon_outlined, size: 18),
                  label: const Text('Keep it working'),
                ),
              ),
              const SizedBox(width: 10),
            ],
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _busy ? null : _testAgain,
                icon: _busy
                    ? const SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.refresh_rounded, size: 18),
                label: const Text('Test again'),
              ),
            ),
          ],
        ),
      ];
}
