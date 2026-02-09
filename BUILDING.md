# Guide de Build - BPM Detector Pro

Ce projet utilise **PyInstaller** pour créer des exécutables autonomes qui incluent toutes les dépendances (y compris FFmpeg).

## 1. Préparation
Assurez-vous d'avoir les dépendances installées :
```bash
pip install -r requirements.txt
pip install pyinstaller
```

## 2. Build pour Windows (.exe)
**Note :** Vous devez lancer cette commande depuis un terminal **Windows**.
1. Placez l'exécutable `ffmpeg.exe` dans `packaging/ffmpeg/windows/`.
2. Lancez le build :
```bash
pyinstaller bpm-detector.spec --clean
```
Le fichier `BPM-Detector-Pro.exe` sera généré dans le dossier `dist/`.

## 3. Build pour Linux (Binaire Portable / AppImage)
Depuis Linux :
1. Assurez-vous que `packaging/ffmpeg/linux/ffmpeg` est présent.
2. Lancez le build :
```bash
pyinstaller bpm-detector.spec --clean
```
Le binaire sera dans `dist/BPM-Detector-Pro`. 

### Pour créer une vraie AppImage :
Nous recommandons l'utilisation de `python-appimage` ou simplement de renommer le binaire généré par PyInstaller (qui est déjà autonome). 

Si vous voulez une intégration bureau complète, utilisez un script comme `appimagetool` sur le dossier généré par PyInstaller en mode `onedir`, mais le mode `onefile` (actuel) est généralement suffisant pour un usage portable.

## Pourquoi c'est stable ?
Le build inclut :
- **FFmpeg intégré** : Pas besoin d'installation système.
- **Processus Isolé** : Le moteur de détection tourne dans un processus séparé pour éviter les crashs de l'interface.
- **Optimisation Turbo** : Analyse Hi-Res à 22kHz avec un moteur hybride ACF/Beats.
