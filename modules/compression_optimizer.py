"""
Target File Size Compression Optimizer for CompressX.
Calculates optimal parameters to hit target file sizes for images and videos.
"""

from typing import Dict, Any, Optional
from PIL import Image
from modules.image_compressor import compress_image
from modules.video_compressor import compress_video, get_video_info


def compress_image_to_target_size(
    image: Image.Image,
    target_size_bytes: int,
    output_format: str = "WEBP",
    max_iterations: int = 6
) -> Dict[str, Any]:
    """
    Iteratively searches for optimal quality and scaling to meet target file size.
    """
    low_q = 10
    high_q = 95
    best_result = None
    scale = 1.0

    for _ in range(max_iterations):
        mid_q = (low_q + high_q) // 2
        res = compress_image(image, output_format=output_format, quality=mid_q, resize_scale=scale)
        actual_size = res["size_bytes"]

        if best_result is None or abs(actual_size - target_size_bytes) < abs(best_result["size_bytes"] - target_size_bytes):
            best_result = res

        if actual_size > target_size_bytes:
            high_q = mid_q - 1
            if high_q < 15 and scale > 0.6:
                # Need resolution reduction to hit target
                scale *= 0.8
                low_q = 20
                high_q = 80
        else:
            low_q = mid_q + 1

        if low_q > high_q:
            break

    diff = best_result["size_bytes"] - target_size_bytes
    best_result["target_size_bytes"] = target_size_bytes
    best_result["target_diff_bytes"] = diff
    best_result["target_achieved"] = best_result["size_bytes"] <= target_size_bytes * 1.15

    return best_result


def calculate_video_target_bitrate(
    duration_sec: float,
    target_size_bytes: int,
    audio_bitrate_kbps: int = 96
) -> int:
    """
    Computes required video bitrate in kbps:
    Total bits = target_bytes * 8
    Video bits = Total bits - Audio bits
    Video kbps = Video bits / (duration * 1000)
    """
    if duration_sec <= 0:
        return 500

    total_bits = target_size_bytes * 8
    audio_bits = audio_bitrate_kbps * 1000 * duration_sec
    video_bits = max(50_000 * duration_sec, total_bits - audio_bits)

    video_kbps = int(video_bits / (duration_sec * 1000))
    # Keep within practical bounds
    return max(150, min(video_kbps, 15_000))


def compress_video_to_target_size(
    input_path: str,
    output_path: str,
    target_size_bytes: int
) -> Dict[str, Any]:
    """
    Compresses video to target size using calculated bitrate and adaptive resolution.
    """
    info = get_video_info(input_path)
    duration = info["duration"]
    if duration <= 0:
        duration = 10.0

    target_kb = target_size_bytes / 1024.0
    audio_kbps = 64 if target_kb < 5000 else 96
    video_kbps = calculate_video_target_bitrate(duration, target_size_bytes, audio_bitrate_kbps=audio_kbps)

    # Automatically downscale resolution if bitrate is very low
    res_choice = "Original"
    if video_kbps < 400:
        res_choice = "480p"
    elif video_kbps < 900:
        res_choice = "720p"

    res = compress_video(
        input_path=input_path,
        output_path=output_path,
        codec="libx264",
        custom_bitrate_kbps=video_kbps,
        target_resolution=res_choice,
        audio_bitrate_kbps=audio_kbps
    )

    diff = res["compressed_size"] - target_size_bytes
    res["target_size_bytes"] = target_size_bytes
    res["target_diff_bytes"] = diff
    res["target_achieved"] = res["compressed_size"] <= target_size_bytes * 1.25

    return res
