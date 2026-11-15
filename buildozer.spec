[app]
title = Flight Echo
package.name = myradar
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,ttc
version = 1.0.1

# 不要去锁死 cython，镜像自带了完美兼容的版本
# 去掉 android，因为它会在编译时报错
requirements = python3,kivy==2.2.1,requests,urllib3,plyer

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 31
android.minapi = 24
# 这行必须加，补齐之前缺失的 NDK API 设置
android.ndk_api = 24
android.archs = arm64-v8a
# 删掉 android.ndk = 23b，让 Docker 镜像自动使用它内部自带的 NDK，彻底消除版本冲突
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
