import 'package:dio/dio.dart';
import 'package:prognos/core/handles/handle_models.dart';
import 'package:prognos/core/handles/handles_api.dart';

/// Fake [HandlesApi] — canned list/initiate and a configurable confirm outcome.
class FakeHandlesApi extends HandlesApi {
  FakeHandlesApi({
    this.handles = const [],
    this.confirmError,
    this.initiation,
  }) : super(Dio());

  List<Handle> handles;
  ConfirmException? confirmError;
  HandleInitiation? initiation;

  @override
  Future<List<Handle>> list() async => handles;

  @override
  Future<HandleInitiation> initiate(String handle) async =>
      initiation ??
      HandleInitiation(
        handleId: 'h1',
        handle: handle,
        token: 'PGS-ABC123',
        expiresAt: DateTime.now().toUtc().add(const Duration(hours: 1)),
      );

  @override
  Future<void> confirm(String handleId) async {
    if (confirmError != null) throw confirmError!;
  }

  @override
  Future<void> unlink(String handleId) async {}
}

Handle pendingHandle() => Handle(
      id: 'h1',
      handle: 'tourist',
      isVerified: false,
      isLocked: false,
      verificationToken: 'PGS-ABC123',
      verificationTokenExpiresAt:
          DateTime.now().toUtc().add(const Duration(hours: 1)),
    );

Handle verifiedHandle() =>
    const Handle(id: 'h1', handle: 'tourist', isVerified: true, isLocked: false);

Handle lockedHandle() => Handle(
      id: 'h1',
      handle: 'tourist',
      isVerified: false,
      isLocked: true,
      lockoutExpiresAt: DateTime.now().toUtc().add(const Duration(minutes: 30)),
    );
