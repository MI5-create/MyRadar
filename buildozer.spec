[app]
# ... 其他配置保持不变 ...
requirements = python3,kivy==2.2.1,requests,urllib3,plyer,android,cython==0.29.36

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 31
android.minapi = 24
# 👇 加下面这一行，确保 NDK API 与 minapi 匹配
android.ndk_api = 24 
android.archs = arm64-v8a
android.ndk = 23b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
