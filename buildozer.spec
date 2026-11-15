[app]

# 1. 应用基本信息
title = MyRadar
package.name = myradar
package.domain = org.miradar

# 2. 源码入口
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# 3. 核心依赖（不要在里面写 arch 架构！）
requirements = python3,kivy,requests,urllib3,plyer,android

# 4. 屏幕方向与全屏
orientation = portrait
fullscreen = 0

# 5. Android 专属配置
android.api = 31
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

# 6. 权限配置（GPS + 网络）
android.permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

[buildozer]

# 7. 构建目录与日志级别
build_dir = ./.buildozer
bin_dir = ./bin
log_level = 2
warn_on_root = 1
