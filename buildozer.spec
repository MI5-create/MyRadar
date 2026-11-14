[app]
title = Flight Echo
package.name = myradar
package.domain = org.test
source.dir = .
# 包含字体后缀，防止中文变方块
source.include_exts = py,png,jpg,kv,json,ttf,ttc

version = 1.0.1

# 锁定最稳定的依赖版本
requirements = python3.11,kivy==2.3.0,requests,urllib3,plyer,android

orientation = portrait
fullscreen = 0

# 必须的权限：网络、GPS定位、本地存储
android.permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 33
android.accept_sdk_license = True
android.minapi = 24
android.archs = arm64-v8a
# 锁定官方最适配的 NDK 版本
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
