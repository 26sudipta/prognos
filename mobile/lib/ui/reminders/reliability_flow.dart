import 'dart:io' show Platform;

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';

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

  /// "Didn't get it" → jump straight to the app's settings + one short,
  /// device-aware tip. `openAppSettings()` reliably lands on the app page
  /// (OEM-specific intents are version-fragile), one tap from Battery.
  Future<void> _fixIt() async {
    final tip = await _deviceTip();
    await openAppSettings();
    if (mounted) setState(() => _fixTip = tip);
  }

  /// The one thing that actually matters: keep the OS from putting PROGNOS to
  /// sleep / force-stopping it, which cancels every scheduled alarm. Reminders
  /// already ring through Do Not Disturb (alarm channel), so this is the tip.
  Future<String> _deviceTip() async {
    if (!Platform.isAndroid) {
      return 'On the settings screen, allow the app to send notifications, then '
          'tap Test again.';
    }
    final maker =
        (await DeviceInfoPlugin().androidInfo).manufacturer.toLowerCase();
    if (maker.contains('samsung')) {
      return 'Samsung puts unused apps to sleep and force-stops them, which '
          'cancels their alarms — the usual reason reminders go quiet. Open '
          'Battery → Background usage limits → make sure PROGNOS is NOT under '
          '"Sleeping apps" or "Deep sleeping apps", then add it to "Never '
          'sleeping apps". Then tap Test again.';
    } else if (maker.contains('xiaomi') ||
        maker.contains('redmi') ||
        maker.contains('poco')) {
      return 'Open Battery saver → set PROGNOS to "No restrictions" and turn on '
          'Autostart, so the system stops killing its alarms. Then tap Test again.';
    } else if (maker.contains('oppo') ||
        maker.contains('vivo') ||
        maker.contains('realme')) {
      return 'Open Battery → allow background activity and turn on Auto-launch '
          'for PROGNOS, so the system stops killing its alarms. Then tap Test again.';
    }
    return 'Open Battery → allow unrestricted background activity for PROGNOS, so '
        'the system does not stop it and cancel its alarms. Then tap Test again.';
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
          'It rings even in Do Not Disturb. If it never arrives, tap '
          '"Didn\'t get it" for the one setting to change.',
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
            Expanded(
              child: OutlinedButton(
                onPressed: _busy ? null : _fixIt,
                child: const Text("Didn't get it"),
              ),
            ),
            const SizedBox(width: 10),
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
