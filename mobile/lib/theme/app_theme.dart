import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

/// Dark-first Material 3 theme mirroring the web aesthetic (neutral-dark base,
/// indigo accent, Inter body / JetBrains Mono for numbers & code).
///
/// Light theme is intentionally deferred (this audience lives in dark mode —
/// see the mobile plan). [radius] and [space] keep spacing/rounding consistent
/// across every screen so the design reads as one system.
abstract final class AppTheme {
  static const double radius = 12;
  static const double space = 16;

  static ThemeData get dark {
    const scheme = ColorScheme.dark(
      primary: AppColors.primary500,
      onPrimary: AppColors.textPrimary,
      secondary: AppColors.accent500,
      surface: AppColors.bgSurface,
      onSurface: AppColors.textPrimary,
      error: AppColors.danger500,
      outline: AppColors.borderDefault,
    );

    final baseText = GoogleFonts.interTextTheme(ThemeData.dark().textTheme)
        .apply(bodyColor: AppColors.textPrimary, displayColor: AppColors.textPrimary);

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.bgBase,
      textTheme: baseText,
      canvasColor: AppColors.bgSurface,
      dividerColor: AppColors.borderSubtle,
      splashFactory: InkSparkle.splashFactory,
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.bgBase,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: AppColors.bgSurface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius),
          side: const BorderSide(color: AppColors.borderSubtle),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.bgSurface,
        indicatorColor: AppColors.primary600,
        elevation: 0,
        labelTextStyle: WidgetStateProperty.all(
          baseText.labelSmall?.copyWith(fontWeight: FontWeight.w500),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected)
                ? AppColors.textPrimary
                : AppColors.textMuted,
          ),
        ),
      ),
    );
  }

  /// Monospace style for ratings, counts, and other tabular numbers —
  /// matches the web's JetBrains Mono usage.
  static TextStyle mono({double? fontSize, FontWeight? fontWeight, Color? color}) {
    return GoogleFonts.jetBrainsMono(
      fontSize: fontSize,
      fontWeight: fontWeight,
      color: color,
    );
  }
}
