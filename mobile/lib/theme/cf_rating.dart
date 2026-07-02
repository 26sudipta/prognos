import 'package:flutter/painting.dart';

/// Codeforces rating → colour + rank label. Mirrors the web ladder in
/// `frontend/app/(dashboard)/dashboard/_components/stat-strip.tsx` exactly.
abstract final class CfRating {
  static Color color(int? rating) {
    if (rating == null) return const Color(0xFF94A3B8);
    if (rating >= 2400) return const Color(0xFFF44336); // red — GM+
    if (rating >= 2100) return const Color(0xFFFF8F00); // orange — Master
    if (rating >= 1900) return const Color(0xFFAA46BE); // violet — CM
    if (rating >= 1600) return const Color(0xFF1E88E5); // blue — Expert
    if (rating >= 1400) return const Color(0xFF22D3EE); // cyan — Specialist
    if (rating >= 1200) return const Color(0xFF4CAF50); // green — Pupil
    return const Color(0xFF9E9E9E); // gray — Newbie
  }

  static String rank(int? rating) {
    if (rating == null) return 'Unrated';
    if (rating >= 2400) return 'Grandmaster+';
    if (rating >= 2100) return 'Master';
    if (rating >= 1900) return 'Candidate Master';
    if (rating >= 1600) return 'Expert';
    if (rating >= 1400) return 'Specialist';
    if (rating >= 1200) return 'Pupil';
    return 'Newbie';
  }
}
