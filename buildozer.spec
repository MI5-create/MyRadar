[app]
title = FlightEcho
package.name = myradar
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,TTF,otf
version = 1.0.1

requirements = python3==3.10.12,hostpython3==3.10.12,kivy==2.2.1,cython==0.29.36,requests,urllib3,plyer

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
