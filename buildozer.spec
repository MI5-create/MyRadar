[app]
title = Flight Echo
package.name = myradar
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,ttc

version = 1.0.1

# 必须用 python3，它会自动适配云端环境。别写 python3.11！
requirements = python3,kivy==2.2.1,requests,urllib3,plyer,android

orientation = portrait
fullscreen = 0

# 权限里的逗号后面千万别留空格
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API 降到 31，避开 33 版本的底层 bug
android.api = 31
android.accept_sdk_license = True
android.minapi = 24
# 只保留 64 位，防止内存溢出
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
