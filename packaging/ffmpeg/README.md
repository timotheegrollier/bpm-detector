# FFMPEG binaries

Place a static ffmpeg binary here so the packaged apps work without system installs.

Expected paths:
- Linux: `packaging/ffmpeg/linux/ffmpeg`
- Windows: `packaging/ffmpeg/windows/ffmpeg.exe`

You can also set the `FFMPEG_BINARY` environment variable when running the build
scripts to point to another location.
