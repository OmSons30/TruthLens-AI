package com.truthlens.app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.truthlens.app/overlay"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "startScreenCapture" -> {
                    // Native MediaProjection API initialization logic
                    result.success(true)
                }
                "toggleFloatingWidget" -> {
                    val enable = call.argument<Boolean>("enable") ?: false
                    // Native SYSTEM_ALERT_WINDOW float button service launch
                    result.success(enable)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }
}
