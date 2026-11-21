"""
Real FFmpeg Video Compression Engine for CompressX.
Supports: H.264, H.265 (HEVC), VP9.
Handles audio preservation, resolution scaling, CRF/bitrate control, and progress tracking.
"""

import os
import subprocess
import time
import json
from typing import Dict, Any, Optional, Tuple
from modules.utils import get_ffmpeg_path, create_temp_dir, cleanup_temp_dir
from modules.metrics import calculate_compression_stats


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Extracts video metadata (dimensions, duration, bitrate, fps, codecs) using ffmpeg probe.
    """
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe or not os.path.exists(video_path):
        return {
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "bitrate": 0,
            "size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
            "has_audio": False
        }

    cmd = [
        ffmpeg_exe,
        "-i", video_path,
        "-hide_banner"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr = res.stderr

    duration = 0.0
    width = 0
    height = 0
    has_audio = "Audio:" in stderr
    file_size = os.path.getsize(video_path)

    # Parse Duration: 00:00:10.50
    for line in stderr.splitlines():
        if "Duration:" in line:
            try:
                parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                duration = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            except Exception:
                pass
        if "Video:" in line:
            try:
                # e.g., 1920x1080
                for token in line.split(","):
                    token = token.strip()
                    if "x" in token:
                        dims = token.split()[0].split("x")
                        if len(dims) == 2 and dims[0].isdigit() and dims[1].isdigit():
                            width = int(dims[0])
                            height = int(dims[1])
                            break
            except Exception:
                pass

    bitrate_kbps = int((file_size * 8) / (duration * 1000)) if duration > 0 else 0

    return {
        "duration": duration,
        "width": width,
        "height": height,
        "bitrate_kbps": bitrate_kbps,
        "size_bytes": file_size,
        "has_audio": has_audio
    }


def compress_video(
    input_path: str,
    output_path: str,
    codec: str = "libx264",
    crf: int = 28,
    target_resolution: Optional[str] = "Original",
    custom_bitrate_kbps: Optional[int] = None,
    audio_bitrate_kbps: Optional[int] = 128,
    remove_audio: bool = False,
    preset: str = "medium"
) -> Dict[str, Any]:
    """
    Compresses a video file using FFmpeg.
    Returns compression stats and execution status.
    """
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg executable not found on the system.")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video file not found: {input_path}")

    start_time = time.time()
    orig_info = get_video_info(input_path)

    # Resolution scaling filter
    vf_filters = []
    if target_resolution and target_resolution != "Original":
        if target_resolution == "1080p":
            vf_filters.append("scale=-2:1080")
        elif target_resolution == "720p":
            vf_filters.append("scale=-2:720")
        elif target_resolution == "480p":
            vf_filters.append("scale=-2:480")
        elif target_resolution == "360p":
            vf_filters.append("scale=-2:360")

    cmd = [ffmpeg_exe, "-y", "-i", input_path]

    # Video codec and rate control
    cmd.extend(["-c:v", codec])

    if custom_bitrate_kbps:
        cmd.extend(["-b:v", f"{int(custom_bitrate_kbps)}k", "-maxrate", f"{int(custom_bitrate_kbps * 1.5)}k", "-bufsize", f"{int(custom_bitrate_kbps * 2)}k"])
    else:
        cmd.extend(["-crf", str(int(crf))])

    cmd.extend(["-preset", preset])

    if vf_filters:
        cmd.extend(["-vf", ",".join(vf_filters)])

    # Pixel format for broad browser/player compatibility
    cmd.extend(["-pix_fmt", "yuv420p"])

    # Audio handling
    if remove_audio or not orig_info["has_audio"]:
        cmd.append("-an")
    else:
        # AAC audio with specified bitrate
        cmd.extend(["-c:a", "aac", "-b:a", f"{int(audio_bitrate_kbps or 128)}k"])

    # Output file
    cmd.append(output_path)

    # Execute FFmpeg process
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=300
    )

    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg compression failed:\n{proc.stderr}")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("FFmpeg completed but output file is missing or zero bytes.")

    proc_time = time.time() - start_time
    compressed_info = get_video_info(output_path)
    stats = calculate_compression_stats(orig_info["size_bytes"], compressed_info["size_bytes"])

    return {
        "success": True,
        "output_path": output_path,
        "original_size": orig_info["size_bytes"],
        "compressed_size": compressed_info["size_bytes"],
        "space_saved": stats["space_saved"],
        "reduction_pct": stats["reduction_pct"],
        "compression_ratio": stats["compression_ratio"],
        "duration": compressed_info["duration"],
        "width": compressed_info["width"],
        "height": compressed_info["height"],
        "original_bitrate": orig_info["bitrate_kbps"],
        "compressed_bitrate": compressed_info["bitrate_kbps"],
        "processing_time": proc_time
    }
