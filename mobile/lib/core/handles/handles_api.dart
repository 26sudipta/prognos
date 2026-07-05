import 'package:dio/dio.dart';

import 'handle_models.dart';

/// Wrapper over `/handles/*` on the authed Dio. Confirm maps HTTP status codes
/// to a typed [ConfirmException] so the state machine stays HTTP-agnostic.
class HandlesApi {
  HandlesApi(this._dio);
  final Dio _dio;

  Future<List<Handle>> list() async {
    final res = await _dio.get<List<dynamic>>('/handles');
    return (res.data ?? const [])
        .map((e) => Handle.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<HandleInitiation> initiate(String handle) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/handles/verify/initiate',
      data: {'handle': handle},
    );
    return HandleInitiation.fromJson(res.data ?? const {});
  }

  /// Ask the server to re-check the CF Organization field for the token.
  /// Throws [ConfirmException] on the documented failure codes.
  Future<void> confirm(String handleId) async {
    try {
      await _dio.post('/handles/verify/confirm', data: {'handle_id': handleId});
    } on DioException catch (e) {
      throw _mapConfirmError(e);
    }
  }

  Future<void> unlink(String handleId) => _dio.delete('/handles/$handleId');

  ConfirmException _mapConfirmError(DioException e) {
    final code = e.response?.statusCode;
    final data = e.response?.data;
    switch (code) {
      case 400:
        // detail is a dict: { message, attempts_remaining }
        int? attempts;
        if (data is Map && data['detail'] is Map) {
          attempts = (data['detail']['attempts_remaining'] as num?)?.toInt();
        }
        return ConfirmException(ConfirmFailure.mismatch,
            attemptsRemaining: attempts);
      case 423:
        return const ConfirmException(ConfirmFailure.locked);
      case 410:
        return const ConfirmException(ConfirmFailure.expired);
      case 403:
      case 404:
        return const ConfirmException(ConfirmFailure.notFound);
      default:
        return const ConfirmException(ConfirmFailure.unknown);
    }
  }
}
