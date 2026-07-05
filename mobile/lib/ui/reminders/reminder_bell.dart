import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/reminders/reminders_providers.dart';
import '../../theme/app_colors.dart';
import 'reliability_flow.dart';

/// Per-contest reminder toggle. Filled bell = a reminder is set. The first time
/// a user turns one on (before onboarding), it walks the reliability flow; if
/// they bail out, the star is not set.
class ReminderBell extends ConsumerWidget {
  const ReminderBell({super.key, required this.contestId, this.size = 22});

  final String contestId;
  final double size;

  Future<void> _toggle(BuildContext context, WidgetRef ref) async {
    final starred = ref.read(isStarredProvider(contestId));
    if (!starred) {
      final onboarded = await ref.read(remindersRepositoryProvider).isOnboarded();
      if (!onboarded) {
        if (!context.mounted) return;
        final ok = await runReminderReliabilityFlow(context, ref);
        if (!ok) return; // user declined setup → don't star
      }
    }
    await ref.read(remindersControllerProvider.notifier).toggleStar(contestId);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final starred = ref.watch(isStarredProvider(contestId));
    return IconButton(
      visualDensity: VisualDensity.compact,
      tooltip: starred ? 'Reminder on' : 'Remind me',
      icon: Icon(
        starred ? Icons.notifications_active_rounded : Icons.notifications_none_rounded,
        size: size,
        color: starred ? AppColors.primary400 : AppColors.textMuted,
      ),
      onPressed: () => _toggle(context, ref),
    );
  }
}
