"""
Real Production Image Compression Engine for CompressX.
Supports: JPEG, WebP, AVIF, PNG.
Handles transparency preservation, resizing, and quality control.
"""

import io
import time
import os
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageOps
import numpy as np

# Enable AVIF plugin if available
try:
    import pillow_avif
except ImportError:
    pass

from modules.metrics import calculate_compression_stats, calculate_mse, calculate_psnr, calculate_ssim


def compress_image(
    input_image: Image.Image,
    output_format: str = "WEBP",
    quality: int = 80,
    resize_scale: float = 1.0,
    max_dimension: Optional[int] = None,
    lossless: bool = False
) -> Dict[str, Any]:
    """
    Compresses a PIL Image into the requested format (JPEG, WEBP, AVIF, PNG)
    and returns compressed bytes, dimensions, quality metrics, and time.
    """
    start_time = time.time()
    img = input_image.copy()

    # Preserve EXIF orientation if present
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    orig_w, orig_h = img.size
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

    # 1. Dimension Adjustment / Resizing
    target_w, target_h = orig_w, orig_h
    if resize_scale != 1.0 and 0.1 <= resize_scale <= 1.0:
        target_w = max(1, int(orig_w * resize_scale))
        target_h = max(1, int(orig_h * resize_scale))

    if max_dimension and max(target_w, target_h) > max_dimension:
        ratio = max_dimension / float(max(target_w, target_h))
        target_w = max(1, int(target_w * ratio))
        target_h = max(1, int(target_h * ratio))

    if (target_w, target_h) != (orig_w, orig_h):
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    out_fmt = output_format.upper()
    save_kwargs = {}

    # Format-specific transparency and parameters handling
    if out_fmt in ("JPG", "JPEG"):
        out_fmt = "JPEG"
        if has_alpha:
            # JPEG does not support transparency: composite over solid white canvas safely
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        save_kwargs = {
            "format": "JPEG",
            "quality": int(quality),
            "optimize": True,
            "progressive": True
        }

    elif out_fmt == "WEBP":
        if has_alpha and img.mode != "RGBA":
            img = img.convert("RGBA")
        elif not has_alpha and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        save_kwargs = {
            "format": "WEBP",
            "quality": int(quality),
            "method": 6,
            "lossless": lossless
        }

    elif out_fmt == "AVIF":
        if has_alpha and img.mode != "RGBA":
            img = img.convert("RGBA")
        elif not has_alpha and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        save_kwargs = {
            "format": "AVIF",
            "quality": int(quality)
        }

    elif out_fmt == "PNG":
        if has_alpha and img.mode != "RGBA":
            img = img.convert("RGBA")
        elif not has_alpha and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        save_kwargs = {
            "format": "PNG",
            "optimize": True,
            "compress_level": 9
        }
    else:
        # Fallback default
        out_fmt = "JPEG"
        img = img.convert("RGB")
        save_kwargs = {"format": "JPEG", "quality": int(quality), "optimize": True}

    buffer = io.BytesIO()
    try:
        img.save(buffer, **save_kwargs)
    except Exception as e:
        # In case AVIF or special encoder is unavailable, fallback to WebP
        if out_fmt == "AVIF":
            out_fmt = "WEBP"
            save_kwargs["format"] = "WEBP"
            buffer = io.BytesIO()
            img.save(buffer, **save_kwargs)
        else:
            raise e

    compressed_bytes = buffer.getvalue()
    proc_time = time.time() - start_time

    # Re-open compressed image for metrics comparison
    compressed_img = Image.open(io.BytesIO(compressed_bytes))

    # Calculate image similarity metrics against the original resized
    # Compare in same color mode and size
    ref_orig = input_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
    if ref_orig.mode != compressed_img.mode:
        ref_eval = np.array(ref_orig.convert("RGB"))
        comp_eval = np.array(compressed_img.convert("RGB"))
    else:
        ref_eval = np.array(ref_orig)
        comp_eval = np.array(compressed_img)

    mse_val = calculate_mse(ref_eval, comp_eval)
    psnr_val = calculate_psnr(ref_eval, comp_eval)
    ssim_val = calculate_ssim(ref_eval, comp_eval)

    return {
        "compressed_bytes": compressed_bytes,
        "compressed_image": compressed_img,
        "output_format": out_fmt,
        "quality": quality,
        "width": target_w,
        "height": target_h,
        "original_width": orig_w,
        "original_height": orig_h,
        "size_bytes": len(compressed_bytes),
        "processing_time": proc_time,
        "mse": mse_val,
        "psnr": psnr_val,
        "ssim": ssim_val,
        "has_transparency": has_alpha
    }
