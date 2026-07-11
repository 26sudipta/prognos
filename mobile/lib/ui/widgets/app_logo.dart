import 'package:flutter/material.dart';

import '../../theme/app_colors.dart';

/// The PROGNOS mark — an indigo rounded square with a white trending-up arrow —
/// matching the web favicon (`frontend/app/icon.tsx`) and launcher icon exactly.
/// Single source of truth for the logo so web/app stay consistent.
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 64});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: AppColors.primary500, // #6366F1 — same as the web favicon
        borderRadius: BorderRadius.circular(size * 0.26),
      ),
      child: Icon(
        Icons.trending_up_rounded,
        color: Colors.white,
        size: size * 0.56,
      ),
    );
  }
}

/// The logo with a gentle dim/undim (opacity breathing) — the launch/loading
/// animation shown while the session is restored. Fixed size, no scaling.
/// Respects reduced-motion.
class AnimatedAppLogo extends StatefulWidget {
  const AnimatedAppLogo({super.key, this.size = 56});
  final double size;

  @override
  State<AnimatedAppLogo> createState() => _AnimatedAppLogoState();
}

class _AnimatedAppLogoState extends State<AnimatedAppLogo>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;

  @override
  void initState() {
    super.initState();
    // Construct eagerly in initState — never lazily. A `late final` that is
    // first touched in dispose() builds a Ticker while the element tree is
    // deactivated ("deactivated widget's ancestor is unsafe").
    _c = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    );
    final reduceMotion = WidgetsBinding
        .instance.platformDispatcher.accessibilityFeatures.disableAnimations;
    if (!reduceMotion) _c.repeat(reverse: true);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final reduceMotion = MediaQuery.maybeOf(context)?.disableAnimations ?? false;
    final logo = AppLogo(size: widget.size);
    if (reduceMotion) return logo;

    // Gentle dim ↔ undim only — no size change.
    final opacity = Tween<double>(begin: 0.45, end: 1.0)
        .animate(CurvedAnimation(parent: _c, curve: Curves.easeInOut));
    return FadeTransition(opacity: opacity, child: logo);
  }
}
