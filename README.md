# Compteur Romantique — édition Android (Kivy)

Portage Kivy de l'app PyQt6 originale, pour compilation en `.apk` Android
via GitHub Actions (aucune installation Linux nécessaire).

## Compiler le .apk (GitHub Actions)

1. Crée un dépôt GitHub (public ou privé), par exemple `compteur-romantique-android`.
2. Mets tout le contenu de ce dossier dedans (structure telle quelle, avec le
   dossier `.github/workflows/` inclus).
3. Pousse (`push`) sur la branche `main` :
   ```
   git init
   git add .
   git commit -m "Premier envoi"
   git branch -M main
   git remote add origin https://github.com/<ton-compte>/compteur-romantique-android.git
   git push -u origin main
   ```
4. Va dans l'onglet **Actions** de ton dépôt GitHub. Un workflow "Build APK"
   se lance automatiquement (10–20 minutes la première fois, car Buildozer
   télécharge tout le SDK/NDK Android).
5. Une fois terminé (coche verte ✅), clique sur le run, puis dans
   **Artifacts**, télécharge `compteur-romantique-apk`. C'est un zip
   contenant le `.apk`.
6. Transfère le `.apk` sur un téléphone Android (WhatsApp, câble USB,
   Google Drive...) et installe-le. Android demandera d'autoriser
   « Sources inconnues » la première fois — c'est normal, accepte.

## Relancer une compilation après une modification

Il suffit de repousser sur `main` (`git add . && git commit -m "..." && git push`) ;
le workflow se relance automatiquement à chaque `push`. Tu peux aussi le
relancer manuellement depuis l'onglet Actions → "Build APK" → "Run workflow".

## Tester en local sur PC avant de compiler (optionnel)

Sous Windows :
```
pip install kivy python-dateutil
python main.py
```
Cela ouvre l'app dans une fenêtre desktop, pratique pour vérifier vite fait
avant de lancer une compilation Android (qui prend plus de temps).

## Notes techniques

- La configuration (`countdown_config.json`) est sauvegardée dans le
  stockage privé de l'app (`App.user_data_dir`), donc aucune permission
  Android particulière n'est nécessaire, et les données survivent aux
  mises à jour de l'app.
- Le premier build Buildozer est long (téléchargement du SDK/NDK) ; les
  builds suivants sont plus rapides grâce au cache.
