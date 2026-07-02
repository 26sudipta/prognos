import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';

/// Configured Dio instance for the PROGNOS REST API. Base URL includes the
/// `/api/v1` prefix so callers use bare paths (e.g. `/analytics/dashboard`).
///
/// The auth interceptor (Bearer injection + one-shot refresh-on-401, mirroring
/// the web `_lib/api.ts`) is attached in M1; M0 provides the transport only.
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: '${AppConfig.apiBaseUrl}${AppConfig.apiPrefix}',
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.receiveTimeout,
      contentType: Headers.jsonContentType,
    ),
  );

  if (kDebugMode) {
    dio.interceptors.add(
      LogInterceptor(requestHeader: false, responseHeader: false, responseBody: false),
    );
  }

  return dio;
});
