"""
Power Method Image Block Analysis & Dominant Component Reconstruction Module.
Applies Power Method to Gram matrices A = B^T B of image blocks to produce rank-1 approximations.
NO EVD is used.
"""

import math
import time
import numpy as np
from typing import Dict, Any, Tuple
from modules.power_method import power_method
from modules.metrics import calculate_mse, calculate_psnr, calculate_ssim, calculate_compression_stats


def block_power_method_approximation(
    image_matrix: np.ndarray,
    block_size: int = 8,
    max_iter: int = 30
) -> Dict[str, Any]:
    """
    Divides image into BxB blocks, applies Power Method to B^T B,
    computes dominant singular value sigma_1 = sqrt(lambda_1) and left vector u_1 = B v_1 / sigma_1,
    reconstructs rank-1 block B_approx = sigma_1 * (u_1 @ v_1^T).
    """
    start_time = time.time()
    mat = np.asarray(image_matrix, dtype=np.float64)
    h, w = mat.shape[:2]

    # Pad if not divisible by block_size
    pad_h = (block_size - (h % block_size)) % block_size
    pad_w = (block_size - (w % block_size)) % block_size

    if mat.ndim == 2:
        padded = np.pad(mat, ((0, pad_h), (0, pad_w)), mode="edge")
        reconstructed = np.zeros_like(padded)
        h_pad, w_pad = padded.shape
        sample_history = None

        for i in range(0, h_pad, block_size):
            for j in range(0, w_pad, block_size):
                B = padded[i:i + block_size, j:j + block_size]
                if np.linalg.norm(B) < 1e-8:
                    continue

                A = B.T @ B
                pm = power_method(A, max_iter=max_iter, tol=1e-5)
                if sample_history is None and np.linalg.norm(B) > 10.0:
                    sample_history = pm["history"]

                lam = max(0.0, pm["dominant_eigenvalue"])
                v = pm["dominant_eigenvector"]
                sig = math.sqrt(lam)

                if sig > 1e-8:
                    u = (B @ v) / sig
                    u_norm = np.linalg.norm(u)
                    if u_norm > 1e-8:
                        u = u / u_norm
                    B_approx = sig * np.outer(u, v)
                    reconstructed[i:i + block_size, j:j + block_size] = B_approx

        cropped = np.clip(reconstructed[:h, :w], 0, 255).astype(np.uint8)

    else:
        # Multi-channel RGB
        channels_rec = []
        sample_history = None
        for ch in range(mat.shape[2]):
            padded_ch = np.pad(mat[:, :, ch], ((0, pad_h), (0, pad_w)), mode="edge")
            rec_ch = np.zeros_like(padded_ch)
            h_pad, w_pad = padded_ch.shape

            for i in range(0, h_pad, block_size):
                for j in range(0, w_pad, block_size):
                    B = padded_ch[i:i + block_size, j:j + block_size]
                    if np.linalg.norm(B) < 1e-8:
                        continue
                    A = B.T @ B
                    pm = power_method(A, max_iter=max_iter, tol=1e-5)
                    if sample_history is None and np.linalg.norm(B) > 10.0:
                        sample_history = pm["history"]

                    lam = max(0.0, pm["dominant_eigenvalue"])
                    v = pm["dominant_eigenvector"]
                    sig = math.sqrt(lam)
                    if sig > 1e-8:
                        u = (B @ v) / sig
                        u_norm = np.linalg.norm(u)
                        if u_norm > 1e-8:
                            u = u / u_norm
                        rec_ch[i:i + block_size, j:j + block_size] = sig * np.outer(u, v)

            channels_rec.append(rec_ch[:h, :w])

        cropped = np.clip(np.stack(channels_rec, axis=-1), 0, 255).astype(np.uint8)

    proc_time = time.time() - start_time
    mse_val = calculate_mse(image_matrix, cropped)
    psnr_val = calculate_psnr(image_matrix, cropped)

    # Calculate theoretical mathematical encoding size
    num_blocks = ((h + pad_h) // block_size) * ((w + pad_w) // block_size)
    channels = 1 if mat.ndim == 2 else mat.shape[2]
    # Each rank-1 block stores 1 scalar (sig) + 2*block_size floats (u and v) = 1 + 2*B floats (4 bytes each)
    encoded_bytes = num_blocks * channels * (1 + 2 * block_size) * 4
    orig_bytes = h * w * channels

    stats = calculate_compression_stats(orig_bytes, encoded_bytes)

    return {
        "reconstructed_image": cropped,
        "sample_history": sample_history,
        "mse": mse_val,
        "psnr": psnr_val,
        "processing_time": proc_time,
        "original_bytes": orig_bytes,
        "encoded_bytes": encoded_bytes,
        "compression_ratio": stats["compression_ratio"],
        "reduction_pct": stats["reduction_pct"],
        "num_blocks": num_blocks,
        "block_size": block_size
    }
