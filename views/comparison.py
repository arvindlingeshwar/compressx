"""
CompressX - Side-by-Side Comparison Workspace.
"""

import streamlit as st
from PIL import Image
import io
import os
import numpy as np
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
from modules.utils import format_bytes


def render_comparison():
    st.markdown("## 🔍 Original vs Compressed Comparison")

    has_img = "last_image_result" in st.session_state
    has_vid = "last_video_result" in st.session_state

    if not has_img and not has_vid:
        st.info("No media compressed yet in this session. Go to Image Compressor or Video Compressor to process a file first.")
        return

    mode = st.radio("Media to Inspect:", [m for m in ["Image Comparison", "Video Comparison"] if (m == "Image Comparison" and has_img) or (m == "Video Comparison" and has_vid)], horizontal=True)

    if mode == "Image Comparison" and has_img:
        res = st.session_state["last_image_result"]
        orig_bytes = st.session_state["last_image_orig_bytes"]
        comp_bytes = res["compressed_bytes"]

        orig_pil = Image.open(io.BytesIO(orig_bytes))
        comp_pil = res["compressed_image"]

        st.markdown(f"**Target:** `{st.session_state.get('last_image_name', 'Image')}` | **Format:** `{res['output_format']}` | **Quality:** `{res['quality']}`")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 🖼️ Original ({format_bytes(len(orig_bytes))}, {orig_pil.width}×{orig_pil.height})")
            st.image(orig_pil, use_container_width=True)

        with c2:
            st.markdown(f"#### ⚡ Compressed ({format_bytes(res['size_bytes'])}, {comp_pil.width}×{comp_pil.height})")
            st.image(comp_pil, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🗺️ Absolute Pixel Difference Heatmap")
        try:
            # Match dimensions
            o_arr = np.array(orig_pil.resize(comp_pil.size, Image.Resampling.LANCZOS).convert("L"), dtype=float)
            c_arr = np.array(comp_pil.convert("L"), dtype=float)
            diff = np.abs(o_arr - c_arr)

            if HAS_PLOTLY:
                fig = px.imshow(diff, color_continuous_scale="Viridis", labels=dict(color="Pixel Delta"))
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(15, 23, 42, 0.4)",
                    plot_bgcolor="rgba(30, 41, 59, 0.3)",
                    height=350,
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Show normalized difference as visual image
                norm_diff = np.clip(diff * 5, 0, 255).astype(np.uint8)
                st.image(norm_diff, caption="Enhanced Pixel Delta Map (5x amplified)", use_container_width=True)
        except Exception:
            pass

    elif mode == "Video Comparison" and has_vid:
        res = st.session_state["last_video_result"]
        out_path = res["output_path"]

        st.markdown(f"**File:** `{st.session_state.get('last_video_name', 'Video')}` | **Output:** `{os.path.basename(out_path)}`")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 🎬 Original Stream ({format_bytes(res['original_size'])})")
            st.info("Original stream loaded during compression.")
        with c2:
            st.markdown(f"#### ⚡ Compressed Stream ({format_bytes(res['compressed_size'])})")
            if os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    st.video(f.read())
