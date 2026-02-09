$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv-build"
$Python = $env:PYTHON
if (-not $Python) { $Python = "python" }

if (-not (Test-Path $Venv)) {
  & $Python -m venv $Venv
}

$PyExe = Join-Path $Venv "Scripts\python.exe"
$PyInstaller = Join-Path $Venv "Scripts\pyinstaller.exe"

& $PyExe -m pip install --upgrade pip
& $PyExe -m pip install -r (Join-Path $Root "requirements.txt") pyinstaller

$Ffmpeg = $env:FFMPEG_BINARY
if (-not $Ffmpeg) {
  $Candidate = Join-Path $Root "packaging\ffmpeg\windows\ffmpeg.exe"
  if (Test-Path $Candidate) { $Ffmpeg = $Candidate }
}

if (-not $Ffmpeg) {
  Write-Error "ffmpeg introuvable. Place-le dans packaging\\ffmpeg\\windows\\ffmpeg.exe ou definis FFMPEG_BINARY."
  exit 1
}

& $PyInstaller --noconfirm --clean (Join-Path $Root "bpm-detector.spec")

Write-Host "OK -> $Root\dist\BPM-Detector-Pro.exe"
