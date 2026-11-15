[app]
title = Flight Echo
package.name = myradar
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,ttc
version = 1.0.1

# 关键：锁定 p4a 分支，并明确 Cython 版本
p4a.branch = develop
requirements = python3,kivy==2.2.1,requests,urllib3,plyer,android,cython==0.29.33

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.archs = arm64-v8a
android.ndk = 21e
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
