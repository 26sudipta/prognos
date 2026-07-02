import 'package:flutter/material.dart';

import '../../theme/app_colors.dart';
import '../../theme/app_theme.dart';
import '../widgets/skeleton.dart';

/// Temporary tab body used until the real screens land (M2/M4/M5). Renders with
/// the real design system so M0 demonstrates the visual foundation end-to-end.
class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({
    super.key,
    required this.title,
    required this.icon,
    required this.milestone,
  });

  final String title;
  final IconData icon;
  final String milestone;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700))),
      body: ListView(
        padding: const EdgeInsets.all(AppTheme.space),
        children: [
          Container(
            padding: const EdgeInsets.all(AppTheme.space),
            decoration: BoxDecoration(
              color: AppColors.bgSurface,
              borderRadius: BorderRadius.circular(AppTheme.radius),
              border: Border.all(color: AppColors.borderSubtle),
            ),
            child: Row(
              children: [
                Icon(icon, color: AppColors.primary400),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('$title — arriving in $milestone',
                          style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 2),
                      const Text('Design system ready. Content wired in a later slice.',
                          style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppTheme.space),
          // Preview the loading pattern used across every future screen.
          for (var i = 0; i < 4; i++) ...[
            const Skeleton(height: 64, radius: AppTheme.radius),
            const SizedBox(height: 12),
          ],
        ],
      ),
    );
  }
}
