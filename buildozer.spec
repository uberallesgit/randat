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
source.include_exts = py,png,jpg,kv,atlas,pickle,txt,ttf,json

# (list) Source files to exclude
source.exclude_exts = spec,pyc,pyo,pyc

# (list) List of directory to exclude (give here as much as possible)
source.exclude_dirs = .git,.idea,__pycache__,bin,dist,build,.venv

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (list) Pattern to include files/folders that are in exclude_dirs/exclude_patterns
source.include_patterns = service/*

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy==2.3.1,kivymd==1.1.1,pillow,openpyxl,et-xmlfile

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application (PNG, 512x512)
# icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 24

# (str) Android NDK version to use
#android.ndk = 25b

# (list) Android application meta-data to set (key=value format)
#android.meta_data =

# (str) Android entry point, default is ok
#android.entrypoint = org.kivy.android.PythonActivity

# (list) Android archs to build
android.archs = arm64-v8a, armeabi-v7a

# (list) List of Java .jar files to add to the libs
#android.add_jars = foo.jar,bar.jar

# (list) List of Java files to add to the android project
#android.add_src =

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Enable Gradle build
#android.gradle_dependencies =

# (str) The Android app's theme
#android.apptheme = "@android:style/Theme.NoTitleBar"

# (str) The Android app's activity class
#android.activity_class_name =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage
build_dir = ./.buildozer

# (str) Path to output artifacts
bin_dir = ./bin