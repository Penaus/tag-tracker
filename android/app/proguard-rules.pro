# R8 / ProGuard rules — obfuscate the APK while keeping what must work by name.

-keepattributes *Annotation*, JavascriptInterface, Signature, Exceptions

# WebView <-> JS bridge: these methods are called from JavaScript by name, don't rename/strip.
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Chaquopy (Python-in-Android runtime) — reflection/JNI heavy.
-keep class com.chaquo.python.** { *; }
-dontwarn com.chaquo.python.**

# WorkManager instantiates this by name (also persisted across reboots).
-keep class com.tagtracker.app.PollWorker { *; }
-keep class com.tagtracker.app.RingReceiver { *; }

# Entry points referenced from the manifest are kept automatically; the rest is obfuscated.
-dontwarn javax.annotation.**
