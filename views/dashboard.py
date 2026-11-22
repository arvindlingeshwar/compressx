"""
CompressX - Modern Professional Operations Dashboard.
"""

import streamlit as st
import pandas as pd
from modules.file_manager import get_session_stats
from modules.utils import format_bytes, get_ffmpeg_path
from modules.table_view import render_html_table


def render_dashboard():
    st.markdown("""
    <div class="compressx-hero">
        <div class="hero-heading">COMPRESSX PLATFORM</div>
        <div class="hero-subheading">
            High-efficiency image and video compression suite powered by real codecs (WebP, AVIF, H.264/HEVC) 
            coupled with an explicit Numerical Linear Algebra research module.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Session Metric Cards
    stats = get_session_stats(st.session_state)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Files Compressed</div>
            <div class="stat-value">{stats['total_files']}</div>
            <div class="stat-sub">Active Session</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Storage Saved</div>
            <div class="stat-value">{format_bytes(stats['saved_bytes'])}</div>
            <div class="stat-sub">Disk Space Preserved</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Avg Reduction</div>
            <div class="stat-value">{stats['avg_reduction_pct']:.1f}%</div>
            <div class="stat-sub">Size Percentage Down</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        ff = get_ffmpeg_path()
        status_text = "READY" if ff else "INSTALL NEEDED"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-title">Video Acceleration</div>
            <div class="stat-value" style="font-size: 1.35rem; color: {'#34D399' if ff else '#FBBF24'};">{status_text}</div>
            <div class="stat-sub">FFmpeg Engine</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick Start Hub
    st.markdown("### 🚀 Fast Action Workspaces")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="stat-card">
            <div style="font-size: 1.1rem; font-weight: 700; color: #60A5FA; margin-bottom: 6px;">🖼️ Image Compressor</div>
            <div style="font-size: 0.85rem; color: #CBD5E1; margin-bottom: 14px;">
                JPEG, WebP, AVIF, and PNG. Supports intelligent preset scaling, transparency retention, and side-by-side comparison.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Image Compressor", type="primary", use_container_width=True):
            st.session_state["nav_target"] = "Image Compressor"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="stat-card">
            <div style="font-size: 1.1rem; font-weight: 700; color: #C084FC; margin-bottom: 6px;">🎬 Video Compressor</div>
            <div style="font-size: 0.85rem; color: #CBD5E1; margin-bottom: 14px;">
                H.264 & HEVC/H.265 video compression. Full audio preservation, resolution downscaling, and CRF/bitrate tuning.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Video Compressor", type="primary", use_container_width=True):
            st.session_state["nav_target"] = "Video Compressor"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="stat-card">
            <div style="font-size: 1.1rem; font-weight: 700; color: #34D399; margin-bottom: 6px;">🎯 Target File Size</div>
            <div style="font-size: 0.85rem; color: #CBD5E1; margin-bottom: 14px;">
                Specify an exact target size (e.g. 5 MB for Discord/Email). The optimizer iteratively computes bitrates and scaling.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Target Compressor", type="primary", use_container_width=True):
            st.session_state["nav_target"] = "Target Size Compressor"
            st.rerun()

    st.markdown("---")

    # Recent history table
    st.markdown("### 📋 Recent Compression Tasks")
    history = st.session_state.get("compression_history", [])
    if history:
        table_data = []
        for h in reversed(history[-8:]):
            table_data.append({
                "Type": h.get("type", "Media"),
                "File": h.get("name", "Unknown"),
                "Original": format_bytes(h.get("original_size", 0)),
                "Compressed": format_bytes(h.get("compressed_size", 0)),
                "Reduction": f"{h.get('reduction_pct', 0.0):.1f}%",
                "Ratio": f"{h.get('compression_ratio', 1.0):.2f}x",
                "Time": f"{h.get('processing_time', 0.0):.2f}s"
            })
        render_html_table(table_data)
    else:
        st.info("No files compressed yet in this session. Upload an image or video to get started.")
