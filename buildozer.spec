[app]
title = RANDAT MD
package.name = randatmd
package.domain = org.uberalless
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,pickle,txt
source.exclude_dirs = .git,.idea,__pycache__,bin,dist,build,.venv,backup,specula
source.exclude_patterns = license,images/*/*.jpg
source.include_patterns = service/*

version = 1.0

# Требования зафиксированы правильно
requirements = python3, cython==3.0.11, kivy==2.3.1, kivymd==1.1.1, pillow, openpyxl, et-xmlfile
orientation = portrait
fullscreen = 0
# (bool) Automatically accept the Android SDK licenses
android.accept_sdk_license = True

# Исправленные разрешения для API 33
android.permissions = INTERNET, READ_MEDIA_IMAGES

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer
bin_dir = ./bin
