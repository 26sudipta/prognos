import 'package:flutter/material.dart';

import '../../../theme/app_colors.dart';

/// Thin amber strip shown when the visible data isn't guaranteed fresh — either
/// the server's own contest sync is lagging (`is_stale`) or a refresh just
/// failed and we're showing the offline cache (`fromCacheOnly`).
class ContestBanner extends StatelessWidget {
  const ContestBanner({super.key, required this.offline, required this.stale});

  final bool offline; // showing cache, refresh failed
  final bool stale; // server sync lagging

  @override
  Widget build(BuildContext context) {
    if (!offline && !stale) return const SizedBox.shrink();

    final (icon, text) = offline
        ? (Icons.cloud_off_rounded, 'Offline — showing saved contests')
        : (Icons.warning_amber_rounded, 'Contest data may be out of date');

    return Container(
      width: double.infinity,
      color: AppColors.warning500.withValues(alpha: 0.12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 15, color: AppColors.warning400),
          const SizedBox(width: 8),
          Text(
            text,
            style: const TextStyle(
              color: AppColors.warning400,
              fontSize: 12.5,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
