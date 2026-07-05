# flutter_local_notifications serializes notification details via Gson +
# reflection; R8/shrinking would strip those classes and scheduling silently
# no-ops in release. Keep them. (Harmless if the plugin already ships consumer
# rules; applied only when minification is enabled.)
-keep class com.dexterous.** { *; }
-keep class com.google.gson.** { *; }
-keepattributes *Annotation*, Signature
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# workmanager → androidx.work + Room: WorkManagerInitializer runs at process
# start (via androidx.startup) and reflectively instantiates the Room-generated
# WorkDatabase_Impl. R8 stripped its constructor → NoSuchMethodException →
# instant crash on launch in RELEASE only. Keep androidx.work/room + Room DB
# constructors.
-keep class androidx.work.** { *; }
-keep class androidx.startup.** { *; }
-keep class androidx.room.** { *; }
-keep class * extends androidx.room.RoomDatabase { *; }
-keepclassmembers class * extends androidx.room.RoomDatabase {
    <init>();
}
