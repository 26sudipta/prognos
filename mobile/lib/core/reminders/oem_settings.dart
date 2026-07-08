import 'package:flutter/services.dart';

/// Opens the phone's Auto-start / "never sleeping apps" / power-management screen
/// *directly* (one tap for the user) through a platform channel. On aggressive
/// OEMs (Samsung, Xiaomi, Oppo, Vivo, Huawei…) this whitelist is the difference
/// between a reminder surviving and the OS force-stopping the app and wiping it.
class OemSettings {
  const OemSettings._();

  static const _channel = MethodChannel('io.prognos/oem_settings');

  /// Opens the best-matching settings screen for this device. Returns a vendor
  /// key (`samsung`, `xiaomi`, `oppo`, `oneplus`, `vivo`, `huawei`, `asus`,
  /// `other`) or `app_details` when only the generic app page could be opened —
  /// the caller shows instructions that match the key.
  static Future<String> openAutoStart() async {
    try {
      final key = await _channel.invokeMethod<String>('openAutoStart');
      return key ?? 'app_details';
    } on PlatformException {
      return 'app_details';
    } on MissingPluginException {
      return 'app_details';
    }
  }
}
