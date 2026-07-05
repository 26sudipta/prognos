import 'package:flutter/material.dart';

import '../../../core/contests/contest_format.dart';

/// Compact platform tag — colored abbreviation on a tinted background,
/// mirroring the web `platform-badge`. Works on the dark surface without a
/// white card (tint = platform color at 22% alpha, text = full color).
class PlatformBadge extends StatelessWidget {
  const PlatformBadge(this.platform, {super.key});

  final String platform;

  @override
  Widget build(BuildContext context) {
    final color = platformColor(platform);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.13),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        platformAbbr(platform),
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}
