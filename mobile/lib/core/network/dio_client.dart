import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_api.dart';
import '../auth/token_store.dart';
import '../config/app_config.dart';
import '../storage/secure_store.dart';
import 'auth_interceptor.dart';

BaseOptions _baseOptions() => BaseOptions(
      baseUrl: '${AppConfig.apiBaseUrl}${AppConfig.apiPrefix}',
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.receiveTimeout,
      contentType: Headers.jsonContentType,
    );

/// Bare Dio with **no** auth interceptor — used for the auth endpoints
/// themselves (sign-in, refresh) so token calls never recurse through the
/// Bearer/refresh logic.
final authDioProvider = Provider<Dio>((ref) {
  final dio = Dio(_baseOptions());
  if (kDebugMode) {
    dio.interceptors.add(LogInterceptor(responseBody: false));
  }
  return dio;
});

/// Authenticated Dio for all feature data calls (dashboard, contests,
/// classrooms — M2+). Injects the Bearer token and refreshes once on 401.
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(_baseOptions());
  dio.interceptors.add(
    AuthInterceptor(
      ref.watch(accessTokenStoreProvider),
      ref.watch(secureStoreProvider),
      AuthApi(Dio(_baseOptions())),
    ),
  );
  if (kDebugMode) {
    dio.interceptors.add(LogInterceptor(responseBody: false));
  }
  return dio;
});
