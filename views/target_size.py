"""
CompressX - Target File Size Compression Workspace.
Allows users to specify a strict file size ceiling (e.g., 2 MB, 8 MB, 25 MB).
"""

import streamlit as st
import tempfile
import os
import io
from PIL import Image
from modules.compression_optimizer import compress_image_to_target_size, compress_video_to_target_size
from modules.utils import format_bytes, get_ffmpeg_path
from modules.file_manager import record_history


def render_target_size():
    st.markdown("## 🎯 Compress to Target File Size")
    st.markdown("Fit your images or videos strictly within limits for Discord (8MB/25MB), Gmail (25MB), WhatsApp (16MB), or web upload ceilings.")

    media_type = st.radio("Media Type:", ["Image Target Compression", "Video Target Compression"], horizontal=True)

    if media_type.startswith("Image"):
        col_up, col_ctrl = st.columns([1.2, 1])
        with col_up:
            up_img = st.file_uploader("Upload Image:", type=["jpg", "jpeg", "png", "webp", "bmp"])
        with col_ctrl:
            target_mb = st.number_input("Target Size Ceiling (MB):", min_value=0.05, max_value=50.0, value=0.5, step=0.1)
            target_bytes = int(target_mb * 1024 * 1024)
            out_fmt = st.selectbox("Preferred Format:", ["WEBP", "JPEG", "AVIF"])
            run_btn = st.button("🚀 Fit Image to Target Size", type="primary", use_container_width=True)

        if run_btn and up_img:
            with st.spinner(f"Iteratively optimizing to hit target {target_mb:.2f} MB..."):
                pil_img = Image.open(up_img)
                res = compress_image_to_target_size(pil_img, target_size_bytes=target_bytes, output_format=out_fmt)

                orig_sz = len(up_img.getvalue())
                comp_sz = res["size_bytes"]

                record_history(st.session_state, {
                    "type": "Image (Target)",
                    "name": up_img.name,
                    "original_size": orig_sz,
                    "compressed_size": comp_sz,
                    "reduction_pct": ((orig_sz - comp_sz) / orig_sz) * 100.0,
                    "compression_ratio": (orig_sz / comp_sz) if comp_sz > 0 else 1.0,
                    "processing_time": res["processing_time"]
                })

                st.session_state["target_image_result"] = res
                st.session_state["target_image_orig_bytes"] = up_img.getvalue()

        if "target_image_result" in st.session_state:
            res = st.session_state["target_image_result"]
            comp_sz = res["size_bytes"]
            diff = res["target_diff_bytes"]

            st.markdown("---")
            st.markdown("### 📊 Target Size Evaluation")
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Target Request", format_bytes(res["target_size_bytes"]))
            t2.metric("Actual Result", format_bytes(comp_sz))
            t3.metric("Offset from Target", f"{diff / 1024:.1f} KB", delta=f"{'-' if diff <= 0 else '+'}{abs(diff)/1024:.1f} KB")
            t4.metric("PSNR Quality", f"{res['psnr']:.2f} dB")

            if res["target_achieved"]:
                st.success(f"✅ Successfully matched target ceiling! Output is {format_bytes(comp_sz)}.")
            else:
                st.warning(f"⚠️ Target required strong quantization. Reached {format_bytes(comp_sz)}.")

            c1, c2 = st.columns(2)
            with c1:
                st.image(st.session_state["target_image_orig_bytes"], caption="Original Image", use_container_width=True)
            with c2:
                st.image(res["compressed_bytes"], caption=f"Target Compressed ({format_bytes(comp_sz)})", use_container_width=True)

            ext = res["output_format"].lower()
            st.download_button(
                f"📥 Download Target Compressed Image ({format_bytes(comp_sz)})",
                data=res["compressed_bytes"],
                file_name=f"target_compressed.{ext}",
                mime=f"image/{ext}",
                type="primary",
                use_container_width=True
            )

    else:
        # Video Target Compression
        ffmpeg_bin = get_ffmpeg_path()
        if not ffmpeg_bin:
            st.error("⚠️ FFmpeg required for video target size compression.")
            return

        col_up, col_ctrl = st.columns([1.2, 1])
        with col_up:
            up_vid = st.file_uploader("Upload Video:", type=["mp4", "mov", "avi", "mkv", "webm"])
        with col_ctrl:
            target_vid_mb = st.number_input("Target Video Size (MB):", min_value=1.0, max_value=100.0, value=8.0, step=1.0)
            target_vid_bytes = int(target_vid_mb * 1024 * 1024)
            run_vid_btn = st.button("🚀 Fit Video to Target Size", type="primary", use_container_width=True)

        if run_vid_btn and up_vid:
            with st.spinner(f"Calculating adaptive bitrate and encoding video to ~{target_vid_mb:.1f} MB..."):
                temp_in = os.path.join(tempfile.gettempdir(), f"target_in_{up_vid.name}")
                temp_out = os.path.join(tempfile.gettempdir(), f"target_out_{up_vid.name}.mp4")
                with open(temp_in, "wb") as f:
                    f.write(up_vid.getbuffer())

                res = compress_video_to_target_size(temp_in, temp_out, target_size_bytes=target_vid_bytes)

                record_history(st.session_state, {
                    "type": "Video (Target)",
                    "name": up_vid.name,
                    "original_size": res["original_size"],
                    "compressed_size": res["compressed_size"],
                    "reduction_pct": res["reduction_pct"],
                    "compression_ratio": res["compression_ratio"],
                    "processing_time": res["processing_time"]
                })

                st.session_state["target_video_result"] = res
                st.session_state["target_video_in_path"] = temp_in

        if "target_video_result" in st.session_state:
            res = st.session_state["target_video_result"]
            comp_sz = res["compressed_size"]
            diff = res["target_diff_bytes"]

            st.markdown("---")
            st.markdown("### 📊 Video Target Size Evaluation")
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Target Request", format_bytes(res["target_size_bytes"]))
            t2.metric("Actual Result", format_bytes(comp_sz))
            t3.metric("Offset", f"{diff / (1024*1024):.2f} MB")
            t4.metric("Encoding Bitrate", f"{res['compressed_bitrate']} kbps")

            if res["target_achieved"]:
                st.success(f"✅ Video successfully encoded within target parameters ({format_bytes(comp_sz)}).")
            else:
                st.info(f"Video finalized at {format_bytes(comp_sz)}.")

            out_p = res["output_path"]
            if os.path.exists(out_p):
                with open(out_p, "rb") as f:
                    vid_b = f.read()
                st.video(vid_b)
                st.download_button(
                    f"📥 Download Target Compressed Video ({format_bytes(comp_sz)})",
                    data=vid_b,
                    file_name="target_compressed.mp4",
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True
                )
