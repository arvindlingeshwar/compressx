"""
Mathematical metrics module for CompressX:
- File size compression ratio and savings
- Image quality: MSE, PSNR, SSIM
- STRICT RULE: NO Eigenvalue Decomposition (EVD) is used.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple


def calculate_compression_stats(original_bytes: int, compressed_bytes: int) -> Dict[str, float]:
    """Calculates space saved, reduction percentage, and compression ratio."""
    if original_bytes <= 0:
        return {"space_saved": 0, "reduction_pct": 0.0, "compression_ratio": 1.0}

    space_saved = original_bytes - compressed_bytes
    reduction_pct = (space_saved / original_bytes) * 100.0
    comp_ratio = (original_bytes / compressed_bytes) if compressed_bytes > 0 else 1.0

    return {
        "space_saved": max(0, space_saved),
        "reduction_pct": max(0.0, reduction_pct),
        "compression_ratio": max(1.0, comp_ratio)
    }


def calculate_mse(img1: np.ndarray, img2: np.ndarray) -> float:
    """Mean Squared Error between two images."""
    a = np.asarray(img1, dtype=np.float64)
    b = np.asarray(img2, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"Shape mismatch: {a.shape} vs {b.shape}")
    return float(np.mean((a - b) ** 2))


def calculate_psnr(img1: np.ndarray, img2: np.ndarray, max_val: float = 255.0) -> float:
    """Peak Signal-to-Noise Ratio in dB."""
    mse = calculate_mse(img1, img2)
    if mse <= 1e-12:
        return 100.0
    return float(10.0 * math.log10((max_val ** 2) / mse))


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Structural Similarity Index (SSIM) approximation."""
    x = np.asarray(img1, dtype=np.float64)
    y = np.asarray(img2, dtype=np.float64)
    if x.shape != y.shape:
        return 0.0

    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu_x = np.mean(x)
    mu_y = np.mean(y)
    sigma_x_sq = np.var(x)
    sigma_y_sq = np.var(y)
    sigma_xy = np.mean((x - mu_x) * (y - mu_y))

    num = (2.0 * mu_x * mu_y + c1) * (2.0 * sigma_xy + c2)
    den = (mu_x ** 2 + mu_y ** 2 + c1) * (sigma_x_sq + sigma_y_sq + c2)

    return float(num / den)
