[app]
title = NexDownloader Pro
package.name = nexdownloader
package.domain = org.nextech
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# Requirements - REMOVED extra packages jo issue create kar rahe the
requirements = python3, kivy==2.2.1, kivymd, yt-dlp, android, plyer, pyjnius, certifi

orientation = portrait

# Only essential permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, POST_NOTIFICATIONS

# Remove MANAGE_EXTERNAL_STORAGE - iski zaroorat nahi hai
# Remove gradle_dependencies line - iski bhi zaroorat nahi

android.api = 33
android.minapi = 21
android.target_sdk = 33

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.logcat_filters = *:S python:D
android.copy_libs = 1

# Add this for yt-dlp to work properly
android.add_openssl = True
android.add_sqlite = True