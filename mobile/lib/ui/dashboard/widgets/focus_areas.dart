import 'package:flutter/material.dart';

import '../../../core/analytics/analytics_models.dart';
import '../../../theme/app_colors.dart';

/// "Focus Areas" — weakness signals, colour-coded by type, ordered by the API's
/// score DESC. Mirrors the web weakness cards (renamed "Focus Areas").
class FocusAreas extends StatelessWidget {
  const FocusAreas({super.key, required this.signals});
  final List<WeaknessSignal> signals;

  @override
  Widget build(BuildContext context) {
    if (signals.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: _decoration,
        child: const Center(
          child: Text('No focus areas — nice and balanced.',
              style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
        ),
      );
    }
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: _decoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Focus Areas',
              style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                  fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          for (final s in signals) _SignalTile(signal: s),
        ],
      ),
    );
  }
}

const _decoration = BoxDecoration(
  color: AppColors.bgSurface,
  borderRadius: BorderRadius.all(Radius.circular(14)),
  border: Border.fromBorderSide(BorderSide(color: AppColors.borderSubtle)),
);

class _SignalTile extends StatelessWidget {
  const _SignalTile({required this.signal});
  final WeaknessSignal signal;

  ({Color color, String label}) get _meta => switch (signal.signalType) {
        'low_success' => (color: AppColors.danger400, label: 'Low success'),
        'neglected' => (color: AppColors.warning400, label: 'Neglected'),
        _ => (color: AppColors.accent400, label: 'Under-practiced'),
      };

  @override
  Widget build(BuildContext context) {
    final m = _meta;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.bgSurfaceRaised,
        borderRadius: BorderRadius.circular(10),
        border: Border(left: BorderSide(color: m.color, width: 3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  signal.tag,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: m.color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  m.label,
                  style: TextStyle(
                      color: m.color,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            signal.reason,
            style: const TextStyle(
                color: AppColors.textSecondary, fontSize: 12.5, height: 1.35),
          ),
        ],
      ),
    );
  }
}
