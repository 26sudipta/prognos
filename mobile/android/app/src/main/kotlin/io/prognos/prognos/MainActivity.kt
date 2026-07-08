package io.prognos.prognos

import android.content.ComponentName
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val channel = "io.prognos/oem_settings"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channel)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    // Open the phone's Auto-start / "never sleeping apps" / power screen
                    // directly so the user only has to flip one toggle. Returns a key
                    // for the vendor the UI matched (drives the on-screen instruction),
                    // or "app_details" when no vendor screen resolved.
                    "openAutoStart" -> result.success(openAutoStart())
                    else -> result.notImplemented()
                }
            }
    }

    private fun openAutoStart(): String {
        val maker = Build.MANUFACTURER.lowercase()
        val (vendor, candidates) = when {
            maker.contains("xiaomi") || maker.contains("redmi") || maker.contains("poco") ->
                "xiaomi" to XIAOMI
            maker.contains("oppo") || maker.contains("realme") ->
                "oppo" to OPPO
            maker.contains("oneplus") -> "oneplus" to ONEPLUS
            maker.contains("vivo") || maker.contains("iqoo") -> "vivo" to VIVO
            maker.contains("huawei") || maker.contains("honor") -> "huawei" to HUAWEI
            maker.contains("samsung") -> "samsung" to SAMSUNG
            maker.contains("asus") -> "asus" to ASUS
            else -> "other" to emptyList()
        }

        for (cn in candidates) {
            if (launch(Intent().setComponent(cn))) return vendor
        }

        // Nothing vendor-specific resolved → the app's own details/battery page,
        // which every device has. The caller shows generic guidance for this key.
        val details = Intent(
            Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
            Uri.parse("package:$packageName"),
        )
        launch(details)
        return "app_details"
    }

    /** Launch [intent] only if a component actually resolves it; never throw. */
    private fun launch(intent: Intent): Boolean {
        return try {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            if (packageManager.resolveActivity(intent, 0) == null) return false
            startActivity(intent)
            true
        } catch (_: Exception) {
            false
        }
    }

    companion object {
        private fun cn(pkg: String, cls: String) = ComponentName(pkg, cls)

        // Component names collected from the DontKillMyApp project + vendor docs.
        // Tried in order; the first that resolves on this device is launched.
        private val XIAOMI = listOf(
            cn("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"),
            cn("com.miui.securitycenter", "com.miui.powercenter.PowerSettings"),
        )
        private val OPPO = listOf(
            cn("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"),
            cn("com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity"),
            cn("com.oppo.safe", "com.oppo.safe.permission.startup.StartupAppListActivity"),
            cn("com.coloros.oppoguardelf", "com.coloros.powermanager.fuelgaue.PowerUsageModelActivity"),
        )
        private val ONEPLUS = listOf(
            cn("com.oneplus.security", "com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity"),
        )
        private val VIVO = listOf(
            cn("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity"),
            cn("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager"),
            cn("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"),
        )
        private val HUAWEI = listOf(
            cn("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"),
            cn("com.huawei.systemmanager", "com.huawei.systemmanager.appcontrol.activity.StartupAppControlActivity"),
            cn("com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity"),
        )
        private val SAMSUNG = listOf(
            // "App power management / Background usage limits" holds the Never/
            // Deep-sleeping lists; exported on some One UI builds. If it isn't,
            // launch() falls through to the Battery screen (exported everywhere),
            // which is one tap from "App power management → Never sleeping apps".
            cn("com.samsung.android.lool", "com.samsung.android.sm.battery.ui.setting.AppPowerManagementActivity"),
            cn("com.samsung.android.lool", "com.samsung.android.sm.battery.ui.BatteryActivity"),
            cn("com.samsung.android.sm", "com.samsung.android.sm.ui.battery.BatteryActivity"),
        )
        private val ASUS = listOf(
            cn("com.asus.mobilemanager", "com.asus.mobilemanager.entry.FunctionActivity"),
            cn("com.asus.mobilemanager", "com.asus.mobilemanager.MainActivity"),
        )
    }
}
