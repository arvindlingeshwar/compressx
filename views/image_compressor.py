"""
CompressX - Image Compressor Workspace.
"""

import streamlit as st
import numpy as np
from PIL import Image
import io
import os
from modules.image_compressor import compress_image
from modules.utils import format_bytes
from modules.file_manager import record_history


def render_image_compressor():
    st.markdown("## 🖼️ Image Compressor")
    st.markdown("Compress JPG, PNG, WebP, AVIF, BMP, or TIFF images with instant visual comparison and download.")

    col_upload, col_settings = st.columns([1.2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload Image",
            type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"]
        )

        # Allow test sample fallback
        if uploaded_file is None:
            if st.button("Use Sample Benchmark Image"):
                # Create sample image
                arr = np.zeros((300, 300, 3), dtype=np.uint8)
                arr[:, :] = [45, 60, 110]
                arr[50:250, 50:250] = [210, 140, 40]
                img = Image.fromarray(arr)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.session_state["sample_image_bytes"] = buf.getvalue()
                st.session_state["sample_image_name"] = "sample_pattern.png"

        curr_bytes = None
        curr_name = ""
        if uploaded_file is not None:
            curr_bytes = uploaded_file.getvalue()
            curr_name = uploaded_file.name
        elif "sample_image_bytes" in st.session_state:
            curr_bytes = st.session_state["sample_image_bytes"]
            curr_name = st.session_state["sample_image_name"]

        if curr_bytes:
            orig_pil = Image.open(io.BytesIO(curr_bytes))
            st.image(orig_pil, caption=f"Original: {curr_name} ({format_bytes(len(curr_bytes))}, {orig_pil.width}×{orig_pil.height})", use_container_width=True)

    with col_settings:
        st.markdown("### ⚙️ Compression Profile")
        preset = st.selectbox(
            "Intelligent Preset:",
            ["Balanced (Recommended)", "Maximum Quality", "High Compression", "Smallest File Size", "Custom"]
        )

        # Map preset to parameters
        default_fmt = "WEBP"
        default_q = 80
        default_scale = 1.0

        if preset == "Maximum Quality":
            default_q = 92
            default_fmt = "WEBP"
        elif preset == "Balanced (Recommended)":
            default_q = 80
            default_fmt = "WEBP"
        elif preset == "High Compression":
            default_q = 60
            default_scale = 0.85
        elif preset == "Smallest File Size":
            default_q = 40
            default_scale = 0.65

        fmt = st.selectbox("Output Format:", ["WEBP", "JPEG", "AVIF", "PNG"], index=["WEBP", "JPEG", "AVIF", "PNG"].index(default_fmt))

        if preset == "Custom":
            quality = st.slider("Quality (1-100):", 10, 100, default_q)
            scale = st.slider("Resolution Scale:", 0.2, 1.0, default_scale, step=0.05)
        else:
            quality = default_q
            scale = default_scale
            st.info(f"Preset configured: Quality = {quality}, Resolution Scale = {scale}x")

        run_compress = st.button("🚀 Compress Image", type="primary", use_container_width=True)

    if run_compress and curr_bytes:
        with st.spinner("Applying image codec compression..."):
            orig_pil = Image.open(io.BytesIO(curr_bytes))
            res = compress_image(
                input_image=orig_pil,
                output_format=fmt,
                quality=quality,
                resize_scale=scale
            )

            # Record task in session
            orig_size = len(curr_bytes)
            comp_size = res["size_bytes"]
            record_history(st.session_state, {
                "type": "Image",
                "name": curr_name,
                "original_size": orig_size,
                "compressed_size": comp_size,
                "reduction_pct": ((orig_size - comp_size) / orig_size) * 100.0,
                "compression_ratio": (orig_size / comp_size) if comp_size > 0 else 1.0,
                "processing_time": res["processing_time"]
            })

            st.session_state["last_image_result"] = res
            st.session_state["last_image_orig_bytes"] = curr_bytes
            st.session_state["last_image_name"] = curr_name

    # Display Results
    if "last_image_result" in st.session_state:
        res = st.session_state["last_image_result"]
        orig_size = len(st.session_state["last_image_orig_bytes"])
        comp_size = res["size_bytes"]
        saved = max(0, orig_size - comp_size)
        red_pct = (saved / orig_size * 100.0) if orig_size > 0 else 0.0

        st.markdown("---")
        st.markdown("### 📊 Compression Results")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Original Size", format_bytes(orig_size))
        m2.metric("Compressed Size", format_bytes(comp_size))
        m3.metric("Reduction", f"{red_pct:.1f}%")
        m4.metric("Comp. Ratio", f"{(orig_size/comp_size):.2f}x" if comp_size > 0 else "1.0x")
        m5.metric("PSNR Quality", f"{res['psnr']:.2f} dB")
        m6.metric("Latency", f"{res['processing_time']*1000:.1f} ms")

        # Side by side visual comparison
        c_orig, c_comp = st.columns(2)
        with c_orig:
            st.markdown(f"**Original** ({res['original_width']}×{res['original_height']} px)")
            st.image(st.session_state["last_image_orig_bytes"], use_container_width=True)

        with c_comp:
            st.markdown(f"**Compressed {res['output_format']}** ({res['width']}×{res['height']} px)")
            st.image(res["compressed_bytes"], use_container_width=True)

        # Download button
        ext = res["output_format"].lower()
        base = os.path.splitext(st.session_state["last_image_name"])[0]
        st.download_button(
            label=f"📥 Download Compressed Image ({format_bytes(comp_size)})",
            data=res["compressed_bytes"],
            file_name=f"{base}_compressed.{ext}",
            mime=f"image/{ext}",
            type="primary",
            use_container_width=True
        )
