[app]

# (str) Title of your application
title = Cards

# (str) Package name
package.name = cards

# (str) Package domain (needed for android/ios packaging)
package.domain = uk.brzozowski

# (str) Source code where the main.py live
source.dir = app/

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 2)
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma seperated e.g. requirements = sqlite3,kivy
requirements = sqlite3,pil,plyer,openssl,ws4py,twisted,txws,setuptools,websocket-client,qrcode,jsonpickle,kivy

# (list) Garden requirements
garden_requirements = qrcode

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/icon.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,INTERNET

# (int) Android API to use
android.api = 18

# (int) Minimum API required
android.minapi = 16

# (int) Android SDK version to use
#android.sdk = 23

# (str) Android NDK version to use
#android.ndk = 9c

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
android.ndk_path = /tmp/cs310-piotr/and_res/ndk

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
android.sdk_path = /tmp/cs310-piotr/and_res/sdk

# (str) ANT directory (if empty, it will be automatically downloaded.)
android.ant_path = /tmp/cs310-piotr/and_res/ant

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
android.p4a_dir = /tmp/cs310-piotr/and_res/p4a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
