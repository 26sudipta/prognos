import 'package:flutter/painting.dart';

/// PROGNOS palette — mirrors `frontend/app/globals.css` exactly so the mobile
/// app is visually consistent with the web. Do not invent new shades here; if
/// the web tokens change, change them here too.
abstract final class AppColors {
  // Backgrounds
  static const bgBase = Color(0xFF070B14);
  static const bgSurface = Color(0xFF0F1623);
  static const bgSurfaceRaised = Color(0xFF162032);
  static const bgSurfaceOverlay = Color(0xFF1C2A3F);

  // Borders
  static const borderSubtle = Color(0xFF1E2D45);
  static const borderDefault = Color(0xFF2A3F5C);

  // Primary — indigo
  static const primary400 = Color(0xFF818CF8);
  static const primary500 = Color(0xFF6366F1);
  static const primary600 = Color(0xFF4F46E5);

  // Success — emerald
  static const success400 = Color(0xFF34D399);
  static const success500 = Color(0xFF10B981);

  // Accent — cyan
  static const accent400 = Color(0xFF22D3EE);
  static const accent500 = Color(0xFF06B6D4);

  // Warning & danger
  static const warning400 = Color(0xFFFBBF24);
  static const warning500 = Color(0xFFF59E0B);
  static const danger400 = Color(0xFFF87171);
  static const danger500 = Color(0xFFEF4444);

  // Text
  static const textPrimary = Color(0xFFF1F5F9);
  static const textSecondary = Color(0xFF94A3B8);
  static const textMuted = Color(0xFF64748B);
  static const textDisabled = Color(0xFF334155);
}
