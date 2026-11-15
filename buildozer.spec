[app]
title = Flight Echo
package.name = myradar
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,TTF,otf
version = 1.0.1

requirements = python3,kivy==2.3.0,requests,urllib3,plyer,certifi,openssl

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
