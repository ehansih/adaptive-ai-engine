# Adaptive AI Engine — ProGuard Rules

# ── Capacitor / WebView ───────────────────────────────────────────────────────
-keep class com.getcapacitor.** { *; }
-keep class com.ehansih.adaptiveai.** { *; }
-keepclassmembers class * extends com.getcapacitor.Plugin {
    @com.getcapacitor.annotation.CapacitorPlugin *;
    @com.getcapacitor.annotation.PluginMethod *;
}

# Keep WebView JS interface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# ── Android core ──────────────────────────────────────────────────────────────
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes Exceptions
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Service

# ── Remove logging in release ─────────────────────────────────────────────────
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# ── OkHttp / network ──────────────────────────────────────────────────────────
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# ── Crash safety ──────────────────────────────────────────────────────────────
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
