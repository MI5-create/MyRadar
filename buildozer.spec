[app]
# APP 名称
title = Flight Echo
# 包名（不要轻易改，否则手机会当成新APP）
package.name = myradar
package.domain = org.test

source.dir = .
# ⚠️ 核心修复：必须包含 ttf,ttc，否则打包后没有中文字体
source.include_exts = py,png,jpg,kv,json,ttf,ttc

version = 1.0.1

# ⚠️ 核心：依赖库
requirements = python3==3.10.12,kivy==2.3.0,Cython==0.29.33,jnius>=1.4.0,requests,urllib3,plyer,android
android.ndk = 25b

# 竖屏
orientation = portrait
fullscreen = 0

# ⚠️ 核心：必须加上网络、GPS定位、本地存储权限
android.permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# 目标安卓版本
android.api = 33
android.accept_sdk_license = True
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
# 强制使用国内 Gitee 镜像下载 p4a，防止 GitHub 网络断流
p4a.url = https://gitee.com/mirrors/python-for-android.git
p4a.branch = master

# APP 图标（如果你在文件夹里放了 icon.png，把这行前面的 # 删掉）
# icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
