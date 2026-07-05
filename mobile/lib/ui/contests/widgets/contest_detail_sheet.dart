import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/contests/contest_format.dart';
import '../../../core/db/app_database.dart';
import '../../../theme/app_colors.dart';
import '../../reminders/reminder_bell.dart';
import 'contest_countdown.dart';
import 'platform_badge.dart';

/// Bottom-sheet contest detail. Full metadata + "Open contest" (browser).
/// Presented via [show]; dismiss by swipe / backdrop / the close button.
class ContestDetailSheet extends StatelessWidget {
  const ContestDetailSheet({super.key, required this.contest});

  final Contest contest;

  static Future<void> show(BuildContext context, Contest contest) {
    return showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.bgSurface,
      isScrollControlled: true,
      showDragHandle: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => ContestDetailSheet(contest: contest),
    );
  }

  Future<void> _open(BuildContext context) async {
    final uri = Uri.tryParse(contest.url);
    final messenger = ScaffoldMessenger.of(context);
    final ok = uri != null &&
        await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!ok) {
      messenger.showSnackBar(
        const SnackBar(content: Text('Could not open the contest link')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = platformColor(contest.platform);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                PlatformBadge(contest.platform),
                const SizedBox(width: 8),
                Text(
                  platformDisplayName(contest.platform),
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
                const Spacer(),
                ReminderBell(contestId: contest.id),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              contest.name,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.w700,
                height: 1.25,
              ),
            ),
            const SizedBox(height: 16),
            ContestCountdown(contest: contest, large: true),
            const SizedBox(height: 20),
            _DetailRow(
              icon: Icons.event_rounded,
              label: 'Starts',
              value: formatLocalDateTimeLong(contest.startTime),
            ),
            _DetailRow(
              icon: Icons.event_available_rounded,
              label: 'Ends',
              value: formatLocalEndLabel(contest.startTime, contest.endTime),
            ),
            _DetailRow(
              icon: Icons.hourglass_bottom_rounded,
              label: 'Duration',
              value: formatDuration(contest.durationSeconds),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: color,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () => _open(context),
                icon: const Icon(Icons.open_in_new_rounded, size: 18),
                label: const Text('Open contest'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Icon(icon, size: 17, color: AppColors.textMuted),
          const SizedBox(width: 12),
          SizedBox(
            width: 72,
            child: Text(
              label,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
