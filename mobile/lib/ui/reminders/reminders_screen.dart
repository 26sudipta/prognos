import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/contests/contest_format.dart';
import '../../core/contests/contests_providers.dart';
import '../../core/db/app_database.dart';
import '../../core/reminders/reminders_providers.dart';
import '../../theme/app_colors.dart';
import 'reliability_flow.dart';

/// Reminder settings: lead times, per-platform auto-rules, a reliability re-run,
/// and the list of upcoming scheduled reminders.
class RemindersScreen extends ConsumerWidget {
  const RemindersScreen({super.key});

  // Offered lead times (minutes) → label.
  static const _leadOptions = <int, String>{
    1440: '1d',
    60: '1h',
    30: '30m',
    15: '15m',
    5: '5m',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(remindersControllerProvider);
    final platforms = ref.watch(availablePlatformsProvider);
    final contests = ref.watch(contestsProvider).value?.contests ?? const [];
    final nameById = {for (final c in contests) c.id: c};

    return Scaffold(
      appBar: AppBar(title: const Text('Reminders')),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (state) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _SectionLabel('LEAD TIMES'),
            const _Hint('When reminders fire before a contest starts.'),
            const SizedBox(height: 10),
            _LeadChips(
              selected: state.leadMinutes.toSet(),
              onChanged: (mins) =>
                  ref.read(remindersControllerProvider.notifier).setLeadMinutes(mins),
            ),
            const SizedBox(height: 24),
            _SectionLabel('AUTO-REMIND BY PLATFORM'),
            const _Hint('Automatically remind me for every contest on a platform.'),
            const SizedBox(height: 6),
            if (platforms.isEmpty)
              const _Hint('No platforms yet — open the Contests tab first.')
            else
              for (final p in platforms)
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  activeThumbColor: AppColors.primary400,
                  title: Text(platformDisplayName(p),
                      style: const TextStyle(color: AppColors.textPrimary)),
                  value: state.platformRules[p] ?? false,
                  onChanged: (v) => ref
                      .read(remindersControllerProvider.notifier)
                      .setPlatformRule(p, v),
                ),
            const SizedBox(height: 24),
            _SectionLabel('DELIVERY'),
            const _Hint('Re-check notification, exact-alarm and battery settings.'),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () => runReminderReliabilityFlow(context, ref),
              icon: const Icon(Icons.tune_rounded, size: 18),
              label: const Text('Check reminder settings'),
            ),
            const SizedBox(height: 24),
            _SectionLabel('UPCOMING (${state.upcoming.length})'),
            const SizedBox(height: 6),
            if (state.upcoming.isEmpty)
              const _Hint('Star a contest or enable a platform to schedule reminders.')
            else
              for (final r in state.upcoming.take(30))
                _UpcomingTile(reminder: r, contest: nameById[r.contestId]),
          ],
        ),
      ),
    );
  }
}

class _LeadChips extends StatelessWidget {
  const _LeadChips({required this.selected, required this.onChanged});
  final Set<int> selected;
  final ValueChanged<List<int>> onChanged;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      children: [
        for (final e in RemindersScreen._leadOptions.entries)
          FilterChip(
            label: Text(e.value),
            selected: selected.contains(e.key),
            selectedColor: AppColors.primary500.withValues(alpha: 0.25),
            checkmarkColor: AppColors.primary400,
            backgroundColor: AppColors.bgSurface,
            onSelected: (on) {
              final next = {...selected};
              on ? next.add(e.key) : next.remove(e.key);
              if (next.isEmpty) return; // keep at least one
              onChanged(next.toList());
            },
          ),
      ],
    );
  }
}

class _UpcomingTile extends StatelessWidget {
  const _UpcomingTile({required this.reminder, required this.contest});
  final ScheduledReminder reminder;
  final Contest? contest;

  @override
  Widget build(BuildContext context) {
    final lead = reminder.leadMinutes >= 60
        ? '${reminder.leadMinutes ~/ 60}h before'
        : '${reminder.leadMinutes}m before';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          const Icon(Icons.alarm_rounded, size: 16, color: AppColors.primary400),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  contest?.name ?? 'Contest',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      color: AppColors.textPrimary, fontSize: 14),
                ),
                Text(
                  '$lead · ${formatLocalDateTimeShort(reminder.fireAt)}',
                  style: const TextStyle(
                      color: AppColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Text(
        text,
        style: const TextStyle(
          color: AppColors.textMuted,
          fontSize: 12,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.8,
        ),
      );
}

class _Hint extends StatelessWidget {
  const _Hint(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 4),
        child: Text(
          text,
          style: const TextStyle(
              color: AppColors.textSecondary, fontSize: 12.5, height: 1.3),
        ),
      );
}
