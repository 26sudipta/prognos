import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/contests/contest_format.dart';
import '../../../core/contests/contests_providers.dart';
import '../../../theme/app_colors.dart';

/// Horizontal multi-select platform chips. "All" clears the filter; deselecting
/// every platform auto-restores "All". Chips are derived from the cached window,
/// so filtering works fully offline (client-side).
class PlatformFilterChips extends ConsumerWidget {
  const PlatformFilterChips({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final platforms = ref.watch(availablePlatformsProvider);
    final selected = ref.watch(platformFilterProvider);
    if (platforms.length < 2) return const SizedBox.shrink();

    final notifier = ref.read(platformFilterProvider.notifier);

    return SizedBox(
      height: 40,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _Chip(
            label: 'All',
            color: AppColors.primary400,
            active: selected.isEmpty,
            onTap: () => notifier.state = <String>{},
          ),
          const SizedBox(width: 8),
          for (final p in platforms) ...[
            _Chip(
              label: platformDisplayName(p),
              color: platformColor(p),
              active: selected.contains(p),
              onTap: () {
                final next = {...selected};
                next.contains(p) ? next.remove(p) : next.add(p);
                notifier.state = next;
              },
            ),
            const SizedBox(width: 8),
          ],
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({
    required this.label,
    required this.color,
    required this.active,
    required this.onTap,
  });

  final String label;
  final Color color;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        decoration: BoxDecoration(
          color: active ? color.withValues(alpha: 0.18) : AppColors.bgSurface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: active ? color : AppColors.borderSubtle,
            width: 1,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? color : AppColors.textSecondary,
            fontSize: 13,
            fontWeight: active ? FontWeight.w700 : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}
