$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv-build"
$Python = $env:PYTHON
if (-not $Python) { $Python = "python" }

# Use optimized spec by default, fallback to original
$UseOptimized = $true
if ($env:USE_LEGACY_BUILD -eq "1") { $UseOptimized = $false }

Write-Host "=== BPM Detector Pro - Windows Build ===" -ForegroundColor Cyan
if ($UseOptimized) {
  Write-Host "Mode: OPTIMIZED (fast startup, small size)" -ForegroundColor Green
} else {
  Write-Host "Mode: Legacy (full librosa)" -ForegroundColor Yellow
}

$UseOnedirRaw = $env:USE_ONEDIR
if (-not $UseOnedirRaw) { $UseOnedirRaw = "0" }
$UseOnedir = $UseOnedirRaw.ToLower() -in @("1", "true", "yes", "y")
if ($UseOnedir) {
  Write-Host "Layout: ONEDIR (lower SmartScreen/Defender heuristics)" -ForegroundColor Green
} else {
  Write-Host "Layout: ONEFILE (single file distribution)" -ForegroundColor Yellow
}

# Ensure spec file sees the same layout choice
$env:USE_ONEDIR = if ($UseOnedir) { "1" } else { "0" }

if (-not (Test-Path $Venv)) {
  Write-Host "Creating virtual environment..."
  & $Python -m venv $Venv
}

$PyExe = Join-Path $Venv "Scripts\python.exe"
$PyInstaller = Join-Path $Venv "Scripts\pyinstaller.exe"

function Get-PythonDllInfo {
  param([string]$PyExePath)

  $PyCode = @'
import sys, sysconfig, os, json, glob
ver = f"{sys.version_info.major}{sys.version_info.minor}"
names = [f"python{ver}.dll", "python3.dll"]

found = []

# Env overrides
env_dll = os.environ.get("PYTHON_DLL")
if env_dll:
    for raw in env_dll.split(os.pathsep):
        raw = raw.strip().strip('"')
        if raw and os.path.exists(raw):
            found.append(raw)

env_dir = os.environ.get("PYTHON_DLL_DIR")

# sysconfig hints
cfg_pydll = sysconfig.get_config_var("pythondll")
if cfg_pydll:
    if os.path.isabs(cfg_pydll) and os.path.exists(cfg_pydll):
        found.append(cfg_pydll)
    else:
        if cfg_pydll not in names:
            names.append(cfg_pydll)

python_dir = os.path.dirname(sys.executable)
base_dir = sys.base_prefix
search_paths = [
    python_dir,
    os.path.abspath(os.path.join(python_dir, "..")),
    base_dir,
    os.path.join(base_dir, "DLLs"),
    sys.prefix,
    os.path.join(sys.prefix, "DLLs"),
]
if env_dir:
    search_paths.append(env_dir)
for var in ("BINDIR", "DLLDIR", "LIBDIR", "installed_base", "base", "platbase"):
    val = sysconfig.get_config_var(var)
    if val:
        search_paths.append(val)
seen = set()
search_paths = [p for p in search_paths if p and not (p in seen or seen.add(p))]
seen_found = set()
found = [p for p in found if p and not (p in seen_found or seen_found.add(p))]
for name in names:
    for p in search_paths:
        candidate = os.path.join(p, name)
        if os.path.exists(candidate):
            found.append(candidate)
            break
if not found and base_dir and os.path.exists(base_dir):
    for name in names:
        matches = glob.glob(os.path.join(base_dir, "**", name), recursive=True)
        if matches:
            found.append(matches[0])
            break
print(json.dumps({"version": ver, "names": names, "paths": found}))
'@

  $Json = & $PyExePath -c $PyCode
  if (-not $Json) { return $null }
  try {
    return $Json | ConvertFrom-Json
  } catch {
    return $null
  }
}

Write-Host "Sync version from git tag..."
$UpdateScript = Join-Path $Root "scripts\\update_version.py"
if (Test-Path $UpdateScript) {
  & $PyExe $UpdateScript
} else {
  Write-Warning "update_version.py not found; using existing app_version.py"
}

Write-Host "Installing dependencies..."
& $PyExe -m pip install --upgrade pip --quiet

if ($UseOptimized) {
  Write-Host "Using minimal requirements for optimized build..."
  if (Test-Path (Join-Path $Root "requirements-minimal.txt")) {
    & $PyExe -m pip install -r (Join-Path $Root "requirements-minimal.txt") pyinstaller --quiet
  } else {
    Write-Warning "requirements-minimal.txt not found, using full requirements.txt"
    & $PyExe -m pip install -r (Join-Path $Root "requirements.txt") pyinstaller --quiet
  }
} else {
    & $PyExe -m pip install -r (Join-Path $Root "requirements.txt") pyinstaller --quiet
}

# Check for FFmpeg
$Ffmpeg = $env:FFMPEG_BINARY
if (-not $Ffmpeg) {
  $Candidate = Join-Path $Root "packaging\ffmpeg\windows\ffmpeg.exe"
  if (Test-Path $Candidate) { $Ffmpeg = $Candidate }
}

if (-not $Ffmpeg) {
  Write-Error "ffmpeg introuvable. Place-le dans packaging\\ffmpeg\\windows\\ffmpeg.exe ou definis FFMPEG_BINARY."
  exit 1
}

Write-Host "FFmpeg found: $Ffmpeg"

# UPX is optional (can increase SmartScreen/Defender heuristic flags)
$UseUpx = $env:USE_UPX -eq "1"
$UpxDir = Join-Path $Root "tools\upx"
$UpxExe = Join-Path $UpxDir "upx.exe"

if ($UseUpx) {
  if (-not (Test-Path $UpxExe)) {
    Write-Host "Downloading UPX for better compression..."
    try {
      $UpxUrl = "https://github.com/upx/upx/releases/download/v4.2.2/upx-4.2.2-win64.zip"
      $UpxZip = Join-Path $env:TEMP "upx.zip"
      Invoke-WebRequest -Uri $UpxUrl -OutFile $UpxZip -UseBasicParsing
      New-Item -ItemType Directory -Path $UpxDir -Force | Out-Null
      Expand-Archive -Path $UpxZip -DestinationPath $env:TEMP -Force
      Copy-Item (Join-Path $env:TEMP "upx-4.2.2-win64\upx.exe") $UpxDir
      Remove-Item $UpxZip -Force
      Write-Host "UPX installed successfully" -ForegroundColor Green
    } catch {
      Write-Host "UPX download failed, continuing without compression..." -ForegroundColor Yellow
      $UseUpx = $false
    }
  }
} else {
  Write-Host "UPX disabled (set USE_UPX=1 to enable compression)" -ForegroundColor Yellow
}

# Select spec file
if ($UseOptimized) {
  $SpecFile = Join-Path $Root "bpm-detector-optimized.spec"
  if (-not (Test-Path $SpecFile)) {
    Write-Host "Optimized spec not found, using legacy..." -ForegroundColor Yellow
    $SpecFile = Join-Path $Root "bpm-detector.spec"
  }
} else {
  $SpecFile = Join-Path $Root "bpm-detector.spec"
}

Write-Host "Building with: $SpecFile"

# Build with UPX if available and enabled
$UpxArgs = @()
if ($UseUpx -and (Test-Path $UpxExe)) {
  $UpxArgs = @("--upx-dir", $UpxDir)
  Write-Host "Using UPX compression from: $UpxDir" -ForegroundColor Green
}

& $PyInstaller --noconfirm --clean @UpxArgs $SpecFile

$OutputExeOnefile = Join-Path $Root "dist\BPM-Detector-Pro.exe"
$OutputExeOnedir = Join-Path $Root "dist\BPM-Detector-Pro\BPM-Detector-Pro.exe"

$OutputExe = $null
if ($UseOnedir -and (Test-Path $OutputExeOnedir)) {
  $OutputExe = $OutputExeOnedir
} elseif (Test-Path $OutputExeOnefile) {
  $OutputExe = $OutputExeOnefile
}

if ($OutputExe) {
  # Ensure python DLLs are present next to the .exe (fixes "python3.dll missing" on Windows)
  $TargetDir = Split-Path $OutputExe -Parent
  $DllInfo = Get-PythonDllInfo -PyExePath $PyExe
  if ($DllInfo -and $DllInfo.paths) {
    foreach ($dllPath in $DllInfo.paths) {
      if (-not $dllPath) { continue }
      $dest = Join-Path $TargetDir (Split-Path $dllPath -Leaf)
      if (-not (Test-Path $dest)) {
        Copy-Item $dllPath $TargetDir -Force
      }
    }
  } else {
    Write-Warning "Could not locate python DLLs automatically."
  }

  # If python3.dll is missing but pythonXY.dll exists, duplicate it
  if ($DllInfo -and $DllInfo.version) {
    $PyXY = Join-Path $TargetDir "python$($DllInfo.version).dll"
    $Py3 = Join-Path $TargetDir "python3.dll"
    if ((Test-Path $PyXY) -and (-not (Test-Path $Py3))) {
      Copy-Item $PyXY $Py3 -Force
    }
  }

  # Hard check: fail if python DLLs are still missing in the output dir
  $ExpectedDlls = @("python3.dll")
  if ($DllInfo -and $DllInfo.version) {
    $ExpectedDlls += "python$($DllInfo.version).dll"
  }
  foreach ($dll in $ExpectedDlls) {
    $dllPath = Join-Path $TargetDir $dll
    if (-not (Test-Path $dllPath)) {
      Write-Error "Missing required DLL in output: $dllPath"
      exit 1
    }
  }

  # For ONEFILE builds, create a portable folder that keeps Python DLLs next to the exe
  $PortableDir = $null
  if (-not $UseOnedir) {
    $PortableDir = Join-Path $Root "dist\BPM-Detector-Pro-Portable"
    if (Test-Path $PortableDir) { Remove-Item $PortableDir -Recurse -Force }
    New-Item -ItemType Directory -Path $PortableDir -Force | Out-Null
    Copy-Item $OutputExe $PortableDir -Force
    Get-ChildItem $TargetDir -Filter "python*.dll" -ErrorAction SilentlyContinue | Copy-Item -Destination $PortableDir -Force
    Get-ChildItem $TargetDir -Filter "vcruntime*.dll" -ErrorAction SilentlyContinue | Copy-Item -Destination $PortableDir -Force
  }

  # Optional: create a release ZIP that includes all required files
  $CreateZipRaw = $env:CREATE_ZIP
  if (-not $CreateZipRaw) { $CreateZipRaw = "1" }
  $CreateZip = $CreateZipRaw.ToLower() -in @("1", "true", "yes", "y")
  if ($CreateZip) {
    $ZipOut = Join-Path $Root "dist\BPM-Detector-Pro-Windows.zip"
    if ($UseOnedir) {
      Compress-Archive -Path (Join-Path $Root "dist\BPM-Detector-Pro\*") -DestinationPath $ZipOut -Force
    } else {
      if ($PortableDir) {
        Compress-Archive -Path (Join-Path $PortableDir "*") -DestinationPath $ZipOut -Force
      } else {
        Compress-Archive -Path $OutputExe -DestinationPath $ZipOut -Force
      }
    }
    Write-Host "ZIP created: $ZipOut"
  }

  $Size = (Get-Item $OutputExe).Length / 1MB
  Write-Host ""
  Write-Host "=== BUILD SUCCESS ===" -ForegroundColor Green
  Write-Host "Output: $OutputExe"
  Write-Host ("Size: {0:N1} MB" -f $Size)
} else {
  Write-Error "Build failed - output not found"
  exit 1
}
