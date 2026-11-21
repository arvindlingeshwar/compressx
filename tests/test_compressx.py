"""Unit Tests for CompressX (Image, Video, Power Method, Target Size)."""
import os
import pytest
import numpy as np
from PIL import Image
from modules.power_method import power_method
from modules.power_method_image import block_power_method_approximation
from modules.image_compressor import compress_image
from modules.compression_optimizer import compress_image_to_target_size, calculate_video_target_bitrate
from modules.metrics import calculate_compression_stats, calculate_mse, calculate_psnr
from modules.utils import get_ffmpeg_path


def test_power_method_analytical():
    # Symmetric 2x2 with known dominant lambda = 4.0
    A = np.array([[3.0, 1.0], [1.0, 3.0]])
    res = power_method(A, max_iter=50, tol=1e-7)
    assert res["converged"] is True
    assert pytest.approx(res["dominant_eigenvalue"], rel=1e-4) == 4.0


def test_power_method_rank1_block_approximation():
    # 32x32 synthetic matrix
    img = np.random.RandomState(42).randint(0, 256, (32, 32)).astype(np.uint8)
    res = block_power_method_approximation(img, block_size=8, max_iter=20)
    assert res["reconstructed_image"].shape == (32, 32)
    assert res["psnr"] > 0.0
    assert res["compression_ratio"] > 0.5


def test_real_image_compression_webp():
    # Real image compression test
    img = Image.new("RGB", (100, 100), color=(120, 80, 200))
    res = compress_image(img, output_format="WEBP", quality=75)
    assert res["size_bytes"] > 0
    assert res["output_format"] == "WEBP"
    assert res["width"] == 100
    assert res["height"] == 100


def test_real_image_compression_jpeg_transparency_handling():
    # RGBA image converted to JPEG should composite cleanly over white background
    img = Image.new("RGBA", (80, 80), color=(255, 0, 0, 128))
    res = compress_image(img, output_format="JPEG", quality=80)
    assert res["size_bytes"] > 0
    assert res["output_format"] == "JPEG"


def test_compress_image_target_size():
    img = Image.new("RGB", (200, 200), color=(70, 150, 90))
    # Target 5 KB
    target_bytes = 5 * 1024
    res = compress_image_to_target_size(img, target_size_bytes=target_bytes)
    assert res["size_bytes"] > 0
    assert res["target_size_bytes"] == target_bytes


def test_video_target_bitrate_calculation():
    duration = 10.0
    target_bytes = 5 * 1024 * 1024  # 5 MB
    kbps = calculate_video_target_bitrate(duration, target_bytes, audio_bitrate_kbps=96)
    assert kbps > 300
    assert kbps < 15000


def test_ffmpeg_available():
    path = get_ffmpeg_path()
    assert path is not None
    assert os.path.exists(path)
