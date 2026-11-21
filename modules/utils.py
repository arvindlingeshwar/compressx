"""
Utility functions for CompressX:
- FFmpeg executable resolution (checks system PATH, local bin, imageio-ffmpeg)
- File formatting, byte size formatting
- Temporary file management
"""

import os
import shutil
import tempfile
import subprocess
from typing import Optional

# Common search paths for ffmpeg
CANDIDATE_PATHS = [
    r"C:\Users\aravi\.gemini\antigravity\scratch\bin\ffmpeg.exe",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin", "ffmpeg.exe"),
    "ffmpeg",
]

_CACHED_FFMPEG_PATH: Optional[str] = None


def get_ffmpeg_path() -> Optional[str]:
    """Finds a functional ffmpeg binary or returns None."""
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH and os.path.exists(_CACHED_FFMPEG_PATH):
        return _CACHED_FFMPEG_PATH

    # Check candidates
    for path in CANDIDATE_PATHS:
        if os.path.isabs(path) and os.path.exists(path):
            try:
                res = subprocess.run([path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
                if res.returncode == 0:
                    _CACHED_FFMPEG_PATH = path
                    return path
            except Exception:
                pass
        else:
            # Check PATH
            found = shutil.which(path)
            if found:
                _CACHED_FFMPEG_PATH = found
                return found

    # Fallback to imageio_ffmpeg if available
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            _CACHED_FFMPEG_PATH = exe
            return exe
    except Exception:
        pass

    return None


def format_bytes(size: float) -> str:
    """Format bytes into human-readable B, KB, MB, GB."""
    if size < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def create_temp_dir() -> str:
    """Creates a temporary folder under the system temp directory."""
    temp_dir = tempfile.mkdtemp(prefix="compressx_")
    return temp_dir


def cleanup_temp_dir(path: str):
    """Safely cleans up a temporary directory."""
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass
