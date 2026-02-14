# -*- mode: python ; coding: utf-8 -*-
"""
Optimized PyInstaller spec for minimal size and fast startup.
Target: < 50MB binary with < 5s cold start.
"""
import os
import sys
import sysconfig
import glob
import subprocess
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
try:
    from PyInstaller.utils.hooks import get_python_library_path  # PyInstaller >= 6.3
except Exception:
    try:
        from PyInstaller.compat import get_python_library_path  # Older versions
    except Exception:
        def get_python_library_path():
            return None

block_cipher = None

# Detect platform for FFmpeg bundling
target_os = sys.platform
if target_os.startswith('linux'):
    os_name = 'linux'
    ffmpeg_exe = 'ffmpeg'
elif target_os == 'darwin':
    os_name = 'macos'
    ffmpeg_exe = 'ffmpeg'
elif target_os == 'win32':
    os_name = 'windows'
    ffmpeg_exe = 'ffmpeg.exe'
else:
    os_name = 'linux'
    ffmpeg_exe = 'ffmpeg'

base_dir = os.path.abspath('.')
ffmpeg_src = os.path.join(base_dir, 'packaging', 'ffmpeg', os_name, ffmpeg_exe)

# Sync version from git tag (best effort)
def _sync_version():
    script = os.path.join(base_dir, 'scripts', 'update_version.py')
    if os.path.exists(script):
        try:
            subprocess.run([sys.executable, script], check=False)
        except Exception:
            pass

_sync_version()

# Verify source exists
if not os.path.exists(ffmpeg_src):
    print(f"WARNING: FFmpeg binary not found at {ffmpeg_src}")
    binaries = []
else:
    binaries = [(ffmpeg_src, '.')]

# App icon (Windows prefers .ico)
icon_path = None
if os_name == 'windows':
    icon_candidate = os.path.join(base_dir, 'packaging', 'assets', 'bpm-detector.ico')
    if os.path.exists(icon_candidate):
        icon_path = icon_candidate
    else:
        print(f"WARNING: Icon not found at {icon_candidate}")
elif os_name == 'linux':
    icon_candidate = os.path.join(base_dir, 'packaging', 'assets', 'bpm-detector.png')
    if os.path.exists(icon_candidate):
        icon_path = icon_candidate

# Windows version info (embedded in .exe)
version_file = None
if os_name == 'windows':
    version_candidate = os.path.join(base_dir, 'packaging', 'pyinstaller', 'version_info.txt')
    if os.path.exists(version_candidate):
        version_file = version_candidate
    else:
        print(f"WARNING: Version info not found at {version_candidate}")

# Use onefile by default on Windows for simpler distribution
use_onedir = False
env_use_onedir = os.environ.get('USE_ONEDIR')
if env_use_onedir is not None:
    use_onedir = env_use_onedir.strip().lower() in ('1', 'true', 'yes', 'y')

# Minimal data collection - only soundfile libs
datas = []
binaries += collect_dynamic_libs('soundfile')

# Aggressive exclusions to minimize bundle size
# These are not needed for BPM detection
EXCLUDES = [
    # Heavy ML/scientific packages not needed
    'matplotlib',
    'IPython',
    'notebook',
    'jupyter',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
    'keras',
    'sklearn',
    'pandas',
    
    # Numba JIT compiler (huge, not critical for our use case)
    'numba',
    'llvmlite',

    # Librosa (optional, large). Optimized build uses numpy-only fallback.
    'librosa',
    
    # Testing frameworks
    'pytest',
    'unittest',
    'nose',
    
    # Documentation
    'sphinx',
    'docutils',
    
    # Scipy (not used in optimized build)
    'scipy',
    'scipy.spatial.transform',
    'scipy.io.matlab',
    'scipy.io.arff',
    'scipy.io.netcdf',
    'scipy.io.harwell_boeing',
    'scipy.sparse.linalg._isolve',
    'scipy.sparse.linalg._eigen',
    
    # Unused numpy extras
    'numpy.distutils',
    'numpy.f2py',
    'numpy.testing',
    
    # Network/web (we only use local files)
    'http',
    'urllib3',
    'requests',
    'html',
    'xml',
    
    # Flask (not needed for GUI)
    'flask',
    'werkzeug',
    'jinja2',
    'click',
    
    # Debug/dev tools
    'pdb',
    'trace',
    'cProfile',
    'profile',
    
    # Unused encodings (keep core ones)
    'encodings.idna',
    'encodings.punycode',
    
    # Other unused
    'curses',
    'asyncio',
    'concurrent.futures',
    'multiprocessing.popen_spawn_win32' if os_name != 'windows' else 'multiprocessing.popen_fork',
]

# Only the essential hidden imports
hiddenimports = [
    'soundfile',
    'numpy',
]

def _add_python_dlls(binaries_list):
    if sys.platform != 'win32':
        return
    version_str = f"{sys.version_info.major}{sys.version_info.minor}"
    dll_names = [f'python{version_str}.dll', 'python3.dll']

    # Best-effort: ask PyInstaller for the python DLL path first
    py_dll = get_python_library_path()
    if py_dll and os.path.exists(py_dll):
        print(f"Found python DLL via PyInstaller: {py_dll}")
        binaries_list.append((py_dll, '.'))

    python_dir = os.path.dirname(sys.executable)
    base_dir = sys.base_prefix
    search_paths = [
        python_dir,
        os.path.abspath(os.path.join(python_dir, '..')),  # Common in venv
        base_dir,
        os.path.join(base_dir, 'DLLs'),
        sys.prefix,
        os.path.join(sys.prefix, 'DLLs'),
    ]

    # Add sysconfig-based hints
    for var in ('BINDIR', 'DLLDIR', 'LIBDIR', 'installed_base', 'base', 'platbase'):
        val = sysconfig.get_config_var(var)
        if val:
            search_paths.append(val)

    # De-duplicate paths, keep order
    seen = set()
    search_paths = [p for p in search_paths if p and not (p in seen or seen.add(p))]

    found_any = False
    for dll_name in dll_names:
        found = False
        for path in search_paths:
            dll_path = os.path.join(path, dll_name)
            if os.path.exists(dll_path):
                print(f"Found {dll_name} at {dll_path}, adding to binaries...")
                binaries_list.append((dll_path, '.'))
                found = True
                found_any = True
                break
        if not found:
            print(f"WARNING: Could not find {dll_name} in standard locations.")

    # Last resort: recursive search under base prefix
    if not found_any and base_dir and os.path.exists(base_dir):
        for dll_name in dll_names:
            matches = glob.glob(os.path.join(base_dir, '**', dll_name), recursive=True)
            if matches:
                print(f"Found {dll_name} via recursive search at {matches[0]}, adding to binaries...")
                binaries_list.append((matches[0], '.'))
                break

_add_python_dlls(binaries)

a = Analysis(
    ['bpm_gui_fast.py'],  # Use optimized GUI
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate binaries to save space
seen = set()
a.binaries = [x for x in a.binaries if not (x[0] in seen or seen.add(x[0]))]

# Remove unnecessary datas
a.datas = [x for x in a.datas if not any(
    exc in x[0] for exc in ['__pycache__', '.pyc', 'test', 'example', 'doc']
)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if use_onedir:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='BPM-Detector-Pro',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,  # Strip debug symbols
        upx=True,
        upx_exclude=['vcruntime140.dll', 'python*.dll', 'libffi*.dll'],  # Don't compress critical DLLs
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_path,
        version=version_file,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=True,
        upx=True,
        upx_exclude=['vcruntime140.dll', 'python*.dll', 'libffi*.dll'],
        name='BPM-Detector-Pro',
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='BPM-Detector-Pro',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,  # Strip debug symbols
        upx=True,
        upx_exclude=['vcruntime140.dll', 'python*.dll', 'libffi*.dll'],  # Don't compress critical DLLs
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_path,
        version=version_file,
    )
