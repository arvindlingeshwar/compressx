"""
CompressX - Video Compressor Workspace.
Powered by FFmpeg with H.264, HEVC, resolution downscaling, and audio control.
"""

import streamlit as st
import os
import tempfile
from modules.video_compressor import compress_video, get_video_info
from modules.utils import format_bytes, get_ffmpeg_path
from modules.file_manager import record_history


def render_video_compressor():
    st.markdown("## 🎬 Video Compressor")
    st.markdown("Compress MP4, MOV, AVI, MKV, or WebM video files using high-efficiency FFmpeg codecs.")

    ffmpeg_bin = get_ffmpeg_path()
    if not ffmpeg_bin:
        st.error("⚠️ FFmpeg binary not detected on the system. Please ensure FFmpeg is installed.")
        return

    col_upload, col_params = st.columns([1.2, 1])

    with col_upload:
        uploaded_video = st.file_uploader(
            "Upload Video File:",
            type=["mp4", "mov", "avi", "mkv", "webm"]
        )

        video_path = None
        if uploaded_video is not None:
            # Save uploaded video to temp file for ffmpeg processing
            temp_in = os.path.join(tempfile.gettempdir(), f"input_{uploaded_video.name}")
            with open(temp_in, "wb") as f:
                f.write(uploaded_video.getbuffer())
            video_path = temp_in

            info = get_video_info(video_path)
            st.video(temp_in)
            st.caption(f"Original: {uploaded_video.name} | {format_bytes(info['size_bytes'])} | {info['width']}×{info['height']} | {info['duration']:.1f}s")

    with col_params:
        st.markdown("### ⚙️ Video Encoding Profile")
        preset = st.selectbox(
            "Preset:",
            ["Balanced (Recommended)", "Maximum Quality", "High Compression", "Smallest File Size", "Custom"]
        )

        codec_options = ["H.264 (libx264 - Universal)", "H.265 / HEVC (libx265 - Maximum Efficiency)"]
        selected_codec_label = st.selectbox("Video Codec:", codec_options)
        codec_name = "libx264" if "x264" in selected_codec_label else "libx265"

        default_crf = 28
        default_res = "Original"
        if preset == "Maximum Quality":
            default_crf = 22
            default_res = "Original"
        elif preset == "Balanced (Recommended)":
            default_crf = 28
            default_res = "Original"
        elif preset == "High Compression":
            default_crf = 32
            default_res = "720p"
        elif preset == "Smallest File Size":
            default_crf = 36
            default_res = "480p"

        if preset == "Custom":
            crf = st.slider("Constant Rate Factor (CRF - Lower is higher quality):", 18, 42, default_crf)
            res_choice = st.selectbox("Resolution Scaling:", ["Original", "1080p", "720p", "480p", "360p"], index=0)
        else:
            crf = default_crf
            res_choice = default_res
            st.info(f"Preset configured: CRF = {crf}, Resolution = {res_choice}")

        remove_audio = st.checkbox("Mute / Remove Audio Stream (Saves extra space)")
        run_video_btn = st.button("🚀 Compress Video", type="primary", use_container_width=True)

    if run_video_btn and video_path:
        with st.spinner("Compressing video streams using FFmpeg..."):
            out_file = os.path.join(tempfile.gettempdir(), f"compressed_{os.path.basename(video_path)}.mp4")
            try:
                res = compress_video(
                    input_path=video_path,
                    output_path=out_file,
                    codec=codec_name,
                    crf=crf,
                    target_resolution=res_choice,
                    remove_audio=remove_audio
                )

                # Record task in session
                record_history(st.session_state, {
                    "type": "Video",
                    "name": uploaded_video.name,
                    "original_size": res["original_size"],
                    "compressed_size": res["compressed_size"],
                    "reduction_pct": res["reduction_pct"],
                    "compression_ratio": res["compression_ratio"],
                    "processing_time": res["processing_time"]
                })

                st.session_state["last_video_result"] = res
                st.session_state["last_video_name"] = uploaded_video.name
            except Exception as e:
                st.error(f"Compression error: {e}")

    # Display video output
    if "last_video_result" in st.session_state:
        res = st.session_state["last_video_result"]
        orig_sz = res["original_size"]
        comp_sz = res["compressed_size"]
        out_path = res["output_path"]

        st.markdown("---")
        st.markdown("### 📊 Video Compression Diagnostics")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Original Size", format_bytes(orig_sz))
        m2.metric("Compressed Size", format_bytes(comp_sz))
        m3.metric("Reduction", f"{res['reduction_pct']:.1f}%")
        m4.metric("Comp. Ratio", f"{res['compression_ratio']:.2f}x")
        m5.metric("Bitrate", f"{res['compressed_bitrate']} kbps")
        m6.metric("Time", f"{res['processing_time']:.1f}s")

        c_v1, c_v2 = st.columns(2)
        with c_v1:
            st.markdown(f"**Original Stream** ({format_bytes(orig_sz)})")
            if video_path and os.path.exists(video_path):
                st.video(video_path)
        with c_v2:
            st.markdown(f"**Compressed Stream** ({format_bytes(comp_sz)})")
            if os.path.exists(out_path):
                st.video(out_path)

        # Download button
        if os.path.exists(out_path):
            with open(out_path, "rb") as f:
                video_bytes = f.read()
            st.download_button(
                label=f"📥 Download Compressed Video ({format_bytes(comp_sz)})",
                data=video_bytes,
                file_name=f"compressed_{st.session_state['last_video_name']}.mp4",
                mime="video/mp4",
                type="primary",
                use_container_width=True
            )
