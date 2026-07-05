// Classroom domain models (backend app/schemas/classroom.py). Types that are
// cached for offline (Classroom, Leaderboard) round-trip via toJson.

DateTime? _dt(dynamic v) => v == null ? null : DateTime.parse(v as String).toUtc();
int? _int(dynamic v) => v == null ? null : (v as num).toInt();

class Classroom {
  const Classroom({
    required this.id,
    required this.name,
    required this.myRole,
    required this.memberCount,
    required this.ownerId,
  });

  final String id;
  final String name;
  final String myRole; // 'teacher' | 'student'
  final int memberCount;
  final String ownerId;

  bool get isTeacher => myRole == 'teacher';

  factory Classroom.fromJson(Map<String, dynamic> j) => Classroom(
        id: j['id'] as String,
        name: j['name'] as String,
        myRole: j['my_role'] as String,
        memberCount: (j['member_count'] as num?)?.toInt() ?? 0,
        ownerId: j['owner_id'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'my_role': myRole,
        'member_count': memberCount,
        'owner_id': ownerId,
      };
}

class LeaderboardEntry {
  const LeaderboardEntry({
    required this.rank,
    required this.cfHandle,
    required this.userName,
    required this.cfRating,
    required this.solvedCount,
    required this.currentStreak,
    required this.daysActive30d,
    required this.topTags,
    required this.isMe,
  });

  final int rank;
  final String cfHandle;
  final String userName;
  final int? cfRating;
  final int solvedCount;
  final int currentStreak;
  final int daysActive30d;
  final List<String> topTags;
  final bool isMe;

  static List<String> _tags(dynamic v) {
    if (v is! List) return const [];
    return v
        .whereType<Map>()
        .map((m) => m['tag']?.toString() ?? '')
        .where((s) => s.isNotEmpty)
        .toList();
  }

  factory LeaderboardEntry.fromJson(Map<String, dynamic> j) => LeaderboardEntry(
        rank: (j['rank'] as num).toInt(),
        cfHandle: j['cf_handle'] as String,
        userName: j['user_name'] as String,
        cfRating: _int(j['cf_rating']),
        solvedCount: (j['solved_count'] as num?)?.toInt() ?? 0,
        currentStreak: (j['current_streak'] as num?)?.toInt() ?? 0,
        daysActive30d: (j['days_active_30d'] as num?)?.toInt() ?? 0,
        topTags: _tags(j['top_tags']),
        isMe: j['is_me'] == true,
      );

  Map<String, dynamic> toJson() => {
        'rank': rank,
        'cf_handle': cfHandle,
        'user_name': userName,
        'cf_rating': cfRating,
        'solved_count': solvedCount,
        'current_streak': currentStreak,
        'days_active_30d': daysActive30d,
        'top_tags': [for (final t in topTags) {'tag': t}],
        'is_me': isMe,
      };
}

class Leaderboard {
  const Leaderboard({
    required this.classroomName,
    required this.entries,
    required this.memberCount,
    required this.syncing,
  });

  final String classroomName;
  final List<LeaderboardEntry> entries;
  final int memberCount;
  final bool syncing;

  factory Leaderboard.fromJson(Map<String, dynamic> j) => Leaderboard(
        classroomName: j['classroom_name'] as String? ?? '',
        entries: (j['entries'] as List<dynamic>? ?? const [])
            .map((e) => LeaderboardEntry.fromJson(e as Map<String, dynamic>))
            .toList(),
        memberCount: (j['member_count'] as num?)?.toInt() ?? 0,
        syncing: j['syncing'] == true,
      );

  Map<String, dynamic> toJson() => {
        'classroom_name': classroomName,
        'entries': [for (final e in entries) e.toJson()],
        'member_count': memberCount,
        'syncing': syncing,
      };
}

class Member {
  const Member({
    required this.userId,
    required this.userName,
    required this.cfHandle,
    required this.role,
  });
  final String userId;
  final String userName;
  final String? cfHandle;
  final String role;

  factory Member.fromJson(Map<String, dynamic> j) => Member(
        userId: j['user_id'] as String,
        userName: j['user_name'] as String,
        cfHandle: j['cf_handle'] as String?,
        role: j['role'] as String,
      );
}

class Invite {
  const Invite({
    required this.id,
    required this.token,
    required this.inviteUrl,
    required this.expiresAt,
    required this.isActive,
  });
  final String id;
  final String token;
  final String inviteUrl;
  final DateTime expiresAt;
  final bool isActive;

  factory Invite.fromJson(Map<String, dynamic> j) => Invite(
        id: j['id'] as String,
        token: j['token'] as String,
        inviteUrl: j['invite_url'] as String,
        expiresAt: _dt(j['expires_at'])!,
        isActive: j['is_active'] == true,
      );
}

class JoinPreview {
  const JoinPreview({
    required this.isValid,
    this.classroomName,
    this.memberCount,
    this.errorCode,
  });
  final bool isValid;
  final String? classroomName;
  final int? memberCount;
  final String? errorCode;

  factory JoinPreview.fromJson(Map<String, dynamic> j) => JoinPreview(
        isValid: j['is_valid'] == true,
        classroomName: j['classroom_name'] as String?,
        memberCount: _int(j['member_count']),
        errorCode: j['error_code'] as String?,
      );
}

class CohortTag {
  const CohortTag(this.tag, this.count);
  final String tag;
  final int count;
  factory CohortTag.fromJson(Map<String, dynamic> j) =>
      CohortTag(j['tag'] as String, (j['count'] as num).toInt());
}

class CohortAttendance {
  const CohortAttendance(this.userName, this.cfHandle, this.daysActive30d);
  final String userName;
  final String cfHandle;
  final int daysActive30d;
  factory CohortAttendance.fromJson(Map<String, dynamic> j) => CohortAttendance(
        j['user_name'] as String,
        j['cf_handle'] as String,
        (j['days_active_30d'] as num).toInt(),
      );
}

class CohortAnalytics {
  const CohortAnalytics({
    required this.classAverageRating,
    required this.mostNeglectedTags,
    required this.lowestSuccessTags,
    required this.attendance,
  });
  final double? classAverageRating;
  final List<CohortTag> mostNeglectedTags;
  final List<CohortTag> lowestSuccessTags;
  final List<CohortAttendance> attendance;

  static List<CohortTag> _tags(dynamic v) => (v as List<dynamic>? ?? const [])
      .map((e) => CohortTag.fromJson(e as Map<String, dynamic>))
      .toList();

  factory CohortAnalytics.fromJson(Map<String, dynamic> j) => CohortAnalytics(
        classAverageRating: (j['class_average_rating'] as num?)?.toDouble(),
        mostNeglectedTags: _tags(j['most_neglected_tags']),
        lowestSuccessTags: _tags(j['lowest_success_tags']),
        attendance: (j['student_attendance'] as List<dynamic>? ?? const [])
            .map((e) => CohortAttendance.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
