"""
CompressX - Settings and Temporary Storage Management.
"""

import streamlit as st
import tempfile
import os
import shutil
from modules.utils import get_ffmpeg_path


def render_settings():
    st.markdown("## ⚙️ Application Settings & Session Controls")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🧹 Temporary File Storage")
        temp_dir = tempfile.gettempdir()
        st.write(f"System Temp Directory: `{temp_dir}`")

        if st.button("Clear Temporary Compressed Artifacts", type="secondary"):
            count = 0
            for item in os.listdir(temp_dir):
                if item.startswith("compressx_") or item.startswith("target_") or item.startswith("compressed_"):
                    p = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(p):
                            os.remove(p)
                            count += 1
                        elif os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                            count += 1
                    except Exception:
                        pass
            st.success(f"Cleaned {count} temporary files safely.")

        if st.button("Reset Session History", type="secondary"):
            if "compression_history" in st.session_state:
                st.session_state["compression_history"] = []
            st.success("Session history wiped.")
            st.rerun()

    with c2:
        st.markdown("### 📋 Compression Presets")
        st.markdown("""
        **Default Compression Presets:**
        - Maximum Quality: Image Q=92, Video CRF=22
        - Balanced: Image Q=80 (WebP), Video CRF=28 (H.264)
        - High Compression: Image Q=60 (Scale=0.85x), Video CRF=32 (720p)
        - Smallest File Size: Image Q=40 (Scale=0.65x), Video CRF=36 (480p)
        """)
