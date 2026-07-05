import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/db/app_database.dart';
import '../../../theme/app_colors.dart';

/// Live, self-ticking countdown for a contest, matching the web escalation:
///  • ended       → "Ended" (muted)
///  • live         → "LIVE" pill + time remaining (emerald)
///  • > 24h away   → "Xd Yh"   (secondary)
///  • 1–24h away   → HH:MM:SS   (cyan)
///  • < 1h away    → HH:MM:SS   (red)
///
/// Rebuilds once per second via a single [Timer]; disposed with the widget.
class ContestCountdown extends StatefulWidget {
  const ContestCountdown({super.key, required this.contest, this.large = false});

  final Contest contest;
  final bool large;

  @override
  State<ContestCountdown> createState() => _ContestCountdownState();
}

class _ContestCountdownState extends State<ContestCountdown> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  static String _hms(Duration d) {
    final h = d.inHours;
    final m = d.inMinutes % 60;
    final s = d.inSeconds % 60;
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(h)}:${two(m)}:${two(s)}';
  }

  // Compact "time remaining" for the LIVE state — long events (days) as "Xd",
  // else a normal clock, so the label never blows out the card width.
  static String _compactLeft(Duration d) {
    if (d.inHours >= 24) {
      final days = d.inDays;
      final hours = d.inHours % 24;
      return hours == 0 ? '${days}d' : '${days}d ${hours}h';
    }
    return _hms(d);
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now().toUtc();
    final start = widget.contest.startTime;
    final end = widget.contest.endTime;
    final fs = widget.large ? 22.0 : 14.0;

    // Ended
    if (!now.isBefore(end)) {
      return Text(
        'Ended',
        style: TextStyle(color: AppColors.textMuted, fontSize: fs * 0.8),
      );
    }

    // Live
    if (!now.isBefore(start)) {
      final left = end.difference(now);
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _LivePill(large: widget.large),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              '${_compactLeft(left)} left',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: AppColors.success400,
                fontSize: fs * 0.85,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ),
        ],
      );
    }

    // Upcoming
    final until = start.difference(now);
    if (until.inHours >= 24) {
      final days = until.inDays;
      final hours = until.inHours % 24;
      return Text(
        '${days}d ${hours}h',
        style: TextStyle(
          color: AppColors.textSecondary,
          fontSize: fs,
          fontWeight: FontWeight.w600,
          fontFeatures: const [FontFeature.tabularFigures()],
        ),
      );
    }

    final urgent = until.inHours < 1;
    return Text(
      _hms(until),
      style: TextStyle(
        color: urgent ? AppColors.danger400 : AppColors.accent400,
        fontSize: fs,
        fontWeight: FontWeight.w700,
        fontFeatures: const [FontFeature.tabularFigures()],
      ),
    );
  }
}

class _LivePill extends StatefulWidget {
  const _LivePill({required this.large});
  final bool large;

  @override
  State<_LivePill> createState() => _LivePillState();
}

class _LivePillState extends State<_LivePill>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1100),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final dot = Container(
      width: 7,
      height: 7,
      decoration: const BoxDecoration(
        color: AppColors.success400,
        shape: BoxShape.circle,
      ),
    );
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.success500.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          reduceMotion
              ? dot
              : FadeTransition(opacity: _c, child: dot),
          const SizedBox(width: 6),
          const Text(
            'LIVE',
            style: TextStyle(
              color: AppColors.success400,
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.6,
            ),
          ),
        ],
      ),
    );
  }
}
