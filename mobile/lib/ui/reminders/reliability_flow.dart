import 'dart:io' show Platform;

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../core/reminders/reminders_providers.dart';
import '../../theme/app_colors.dart';

/// First-run reminder opt-in (mobile plan R3). Walks the user through the four
/// things that make on-device alarms actually fire on Android:
///   1. notifications permission (13+)
///   2. exact-alarm grant (12+, not auto-granted on 14+)
///   3. OEM battery-optimisation whitelist (the silent killer on Xiaomi/Oppo/…)
///   4. a test notification so they see it works
/// Returns true if the user completed it (reminders considered on).
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

class _ReliabilitySheet extends ConsumerStatefulWidget {
  const _ReliabilitySheet();

  @override
  ConsumerState<_ReliabilitySheet> createState() => _ReliabilitySheetState();
}

enum _StepState { pending, running, ok, warn }

class _ReliabilitySheetState extends ConsumerState<_ReliabilitySheet> {
  final _steps = <String, _StepState>{
    'Notifications': _StepState.pending,
    'Exact alarms': _StepState.pending,
    'Battery whitelist': _StepState.pending,
    'Test alert': _StepState.pending,
  };
  bool _running = false;
  bool _done = false;
  String? _oemHint;

  Future<void> _run() async {
    setState(() => _running = true);
    final scheduler = ref.read(reminderSchedulerProvider);

    setState(() => _steps['Notifications'] = _StepState.running);
    final notif = await scheduler.requestNotificationsPermission();
    setState(() => _steps['Notifications'] =
        notif ? _StepState.ok : _StepState.warn);

    setState(() => _steps['Exact alarms'] = _StepState.running);
    final exact = await scheduler.requestExactAlarmsPermission();
    setState(
        () => _steps['Exact alarms'] = exact ? _StepState.ok : _StepState.warn);

    setState(() => _steps['Battery whitelist'] = _StepState.running);
    await _batteryStep();

    setState(() => _steps['Test alert'] = _StepState.running);
    if (notif) await scheduler.showTest();
    setState(() => _steps['Test alert'] =
        notif ? _StepState.ok : _StepState.warn);

    setState(() {
      _running = false;
      _done = true;
    });
  }

  Future<void> _batteryStep() async {
    if (!Platform.isAndroid) {
      setState(() => _steps['Battery whitelist'] = _StepState.ok);
      return;
    }
    final info = await DeviceInfoPlugin().androidInfo;
    final maker = info.manufacturer.toLowerCase();
    _oemHint = _oemHints[maker];

    final status = await Permission.ignoreBatteryOptimizations.status;
    if (status.isGranted) {
      setState(() => _steps['Battery whitelist'] = _StepState.ok);
      return;
    }
    final res = await Permission.ignoreBatteryOptimizations.request();
    setState(() => _steps['Battery whitelist'] =
        res.isGranted ? _StepState.ok : _StepState.warn);
  }

  static const _oemHints = <String, String>{
    'xiaomi':
        'On Xiaomi/MIUI: Settings → Apps → PROGNOS → Battery saver → No restrictions, and enable Autostart.',
    'redmi':
        'On Redmi/MIUI: Settings → Apps → PROGNOS → Battery saver → No restrictions, and enable Autostart.',
    'poco':
        'On POCO/MIUI: Settings → Apps → PROGNOS → Battery saver → No restrictions, and enable Autostart.',
    'oppo':
        'On Oppo/ColorOS: Settings → Battery → PROGNOS → allow background activity + Auto-launch.',
    'vivo':
        'On Vivo/Funtouch: Settings → Battery → Background power consumption → allow PROGNOS.',
    'realme':
        'On Realme: Settings → Battery → PROGNOS → allow background activity + Auto-launch.',
    'huawei':
        'On Huawei/EMUI: Settings → Apps → PROGNOS → Battery → Manage manually → enable all.',
    'samsung':
        'On Samsung: Settings → Battery → Background usage limits → remove PROGNOS from “sleeping apps”.',
  };

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.notifications_active_rounded,
                    color: AppColors.primary400),
                SizedBox(width: 10),
                Text(
                  'Turn on contest reminders',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Alerts fire on your device before a contest starts — offline, '
              'screen off. Android needs a few permissions to guarantee they '
              'arrive on time.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13.5, height: 1.4),
            ),
            const SizedBox(height: 16),
            for (final e in _steps.entries) _StepTile(label: e.key, state: e.value),
            if (_oemHint != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.warning500.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  _oemHint!,
                  style: const TextStyle(
                      color: AppColors.warning400, fontSize: 12.5, height: 1.4),
                ),
              ),
            ],
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary500,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: _running
                    ? null
                    : _done
                        ? () => Navigator.of(context).pop(true)
                        : _run,
                child: Text(
                  _running
                      ? 'Setting up…'
                      : _done
                          ? 'Done'
                          : 'Enable reminders',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ),
            if (!_done && !_running)
              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).pop(false),
                  child: const Text('Not now',
                      style: TextStyle(color: AppColors.textMuted)),
                ),
              ),
            if (_done && _hasWarning)
              Center(
                child: TextButton(
                  onPressed: openAppSettings,
                  child: const Text('Some steps need attention — open settings'),
                ),
              ),
          ],
        ),
      ),
    );
  }

  bool get _hasWarning => _steps.values.contains(_StepState.warn);
}

class _StepTile extends StatelessWidget {
  const _StepTile({required this.label, required this.state});
  final String label;
  final _StepState state;

  @override
  Widget build(BuildContext context) {
    final (icon, color) = switch (state) {
      _StepState.pending => (Icons.radio_button_unchecked, AppColors.textMuted),
      _StepState.running => (Icons.pending_rounded, AppColors.accent400),
      _StepState.ok => (Icons.check_circle_rounded, AppColors.success400),
      _StepState.warn => (Icons.error_rounded, AppColors.warning400),
    };
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(width: 12),
          Text(label,
              style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 14.5)),
        ],
      ),
    );
  }
}
