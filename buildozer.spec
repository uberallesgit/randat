[app]
title = RANDAT MD
package.name = randatmd
package.domain = org.uberalless
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,pickle,txt,ttf,otf,json,csv,xlsx
source.exclude_dirs = .git,.idea,__pycache__,bin,dist,build,.venv,backup,specula
source.exclude_patterns = license,images/*/*.jpg
source.include_patterns = service/*,fonts/*,*.py,*.kv,*.json

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
<<<<<<< HEAD
requirements = python3, cython==3.0.11, kivy==git+https://github.com/kivy/kivy.git@2.3.1, kivymd==1.1.1, pillow, openpyxl, et-xmlfile, xlrd, androidstorage4kivy
=======
requirements = python3==3.11.9, hostpython3==3.11.9, cython==0.29.36, kivy==2.2.1, kivymd==1.1.1, pillow, openpyxl, et-xmlfile, xlrd, androidstorage4kivy
#p4a.branch = develop
>>>>>>> b3941e096d2cfeb8ca512d2ee5508cb3e3f0d2e9
orientation = portrait
fullscreen = 0
# (bool) Automatically accept the Android SDK licenses
android.accept_sdk_license = True

# Исправленные разрешения для API 33
android.permissions = INTERNET, ACCESS_NETWORK_STATE, READ_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO
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
