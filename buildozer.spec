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

android.release_artifact = apk
# Путь к вашему keystore
android.keystore = /mnt/c/Users/uber/PycharmProjects/RANDATMD/my-release-key.keystore
# Пароль от keystore
android.keystore_passwd = Reremedy12!@
# Alias ключа (в примере выше — myalias)
android.keyalias = myalias
# Пароль от alias (обычно тот же)
android.keyalias_passwd = Reremedy12!@

# Требования зафиксированы правильно
requirements = python3, cython==3.0.11, kivy==2.3.1, kivymd==1.1.1, pillow, openpyxl, et-xmlfile, xlrd, androidstorage4kivy
orientation = portrait
fullscreen = 0
# (bool) Automatically accept the Android SDK licenses
android.accept_sdk_license = True

# Исправленные разрешения для API 33
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO

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