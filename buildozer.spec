[app]

# (str) Title of your application
title = RANDAT MD

# (str) Package name
package.name = randatmd

# (str) Package domain (needed for android/ios packaging)
package.domain = org.uberalless

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,pickle,txt

# (list) List of directory to exclude (give here as much as possible)
source.exclude_dirs = .git,.idea,__pycache__,bin,dist,build,.venv,backup,specula

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (list) Pattern to include files/folders that are in exclude_dirs/exclude_patterns
source.include_patterns = service/*

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# !!! ЭТА СТРОКА ИСПРАВЛЕНА !!!
requirements = python3,kivy==2.3.0,kivymd==1.1.1,pillow,openpyxl,et-xmlfile,cython==0.29.33
# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (int) Android API to use
# !!! ЭТА СТРОКА ИСПРАВЛЕНА !!!
android.api = 33

# (int) Minimum API required
android.minapi = 21

# !!! ЭТА СТРОКА ДОБАВЛЕНА !!!
android.ndk = 25b

# (list) Android archs to build
# !!! ЭТА СТРОКА ИСПРАВЛЕНА !!!
android.archs = arm64-v8a

# (bool) Enable AndroidX support
android.enable_androidx = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage
build_dir = ./.buildozer

# (str) Path to output artifacts
bin_dir = ./bin

# !!! ЭТА СТРОКА ДОБАВЛЕНА !!!
# Использовать develop-ветку python-for-android для исправления ошибок сборки
p4a.branch = develop
