import 'package:dio/dio.dart';
import 'package:prognos/core/classrooms/classroom_models.dart';
import 'package:prognos/core/classrooms/classrooms_api.dart';

Classroom sampleClassroom({
  String id = 'cl1',
  String name = 'CP 101',
  String role = 'teacher',
  int members = 3,
}) =>
    Classroom(
      id: id,
      name: name,
      myRole: role,
      memberCount: members,
      ownerId: 'owner1',
    );

Leaderboard sampleBoard({List<LeaderboardEntry>? entries, bool syncing = false}) =>
    Leaderboard(
      classroomName: 'CP 101',
      entries: entries ??
          const [
            LeaderboardEntry(
              rank: 1,
              cfHandle: 'tourist',
              userName: 'Gennady',
              cfRating: 3800,
              solvedCount: 5000,
              currentStreak: 100,
              daysActive30d: 30,
              topTags: ['dp', 'graphs'],
              isMe: true,
            ),
          ],
      memberCount: 1,
      syncing: syncing,
    );

/// Fake [ClassroomsApi] — canned list/leaderboard or throws (offline).
class FakeClassroomsApi extends ClassroomsApi {
  FakeClassroomsApi({
    this.classrooms = const [],
    Leaderboard? board,
    this.throwError = false,
  })  : board = board ?? sampleBoard(),
        super(Dio());

  List<Classroom> classrooms;
  final Leaderboard board;
  final bool throwError;

  DioException get _err => DioException(
        requestOptions: RequestOptions(path: '/classrooms'),
        type: DioExceptionType.connectionError,
      );

  @override
  Future<List<Classroom>> list() async {
    if (throwError) throw _err;
    return classrooms;
  }

  @override
  Future<Leaderboard> leaderboard(String id) async {
    if (throwError) throw _err;
    return board;
  }
}
