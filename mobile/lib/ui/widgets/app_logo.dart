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

/// The logo with a gentle breathing pulse — the launch/loading animation shown
/// while the session is restored. Respects reduced-motion.
class AnimatedAppLogo extends StatefulWidget {
  const AnimatedAppLogo({super.key, this.size = 72});
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

    final scale = Tween<double>(begin: 0.92, end: 1.0)
        .animate(CurvedAnimation(parent: _c, curve: Curves.easeInOut));
    final glow = Tween<double>(begin: 0.15, end: 0.45)
        .animate(CurvedAnimation(parent: _c, curve: Curves.easeInOut));

    return AnimatedBuilder(
      animation: _c,
      builder: (context, child) => Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(widget.size * 0.26),
          boxShadow: [
            BoxShadow(
              color: AppColors.primary500.withValues(alpha: glow.value),
              blurRadius: 32,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Transform.scale(scale: scale.value, child: child),
      ),
      child: logo,
    );
  }
}
