[app]
title = Compteur Romantique
package.name = compteurromantique
package.domain = studio.sophitek

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,ttf,mp3,ogg,json
source.include_patterns = assets/*,assets/**/*

version = 3.0

requirements = python3,kivy==2.3.1,python-dateutil

icon.filename = %(source.dir)s/icon.png

orientation = portrait
fullscreen = 0

# Aucune permission nécessaire : la config est sauvegardée dans le
# stockage privé de l'app (App.user_data_dir), pas besoin d'accéder
# au stockage partagé du téléphone.
android.permissions =

android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
