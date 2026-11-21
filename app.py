"""
CompressX - Modern Professional Navigation Shell & Router.
"""

import os
import streamlit as st

# Configure Application Page
st.set_page_config(
    page_title="CompressX – Intelligent Media Compression",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Dark Navy Theme
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 16px 0;">
        <div style="font-size: 1.45rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
            ⚡ CompressX
        </div>
        <div style="font-size: 0.78rem; color: #818CF8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
            Intelligent Media Engine
        </div>
        <div style="font-size: 0.74rem; color: #38BDF8; margin-top: 4px; font-weight: 600;">
            Created by Aravind L
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_labels = [
        "📊 Dashboard",
        "🖼️ Image Compressor",
        "🎬 Video Compressor",
        "🎯 Target Size Compressor",
        "🧮 Power Method Lab",
        "🔍 Compression Comparison",
        "📈 Analytics",
        "⚙️ Settings",
        "ℹ️ About"
    ]
    nav_keys = [
        "Dashboard",
        "Image Compressor",
        "Video Compressor",
        "Target Size Compressor",
        "Power Method Lab",
        "Compression Comparison",
        "Analytics",
        "Settings",
        "About"
    ]

    default_nav = 0
    if "nav_target" in st.session_state and st.session_state["nav_target"] in nav_keys:
        default_nav = nav_keys.index(st.session_state["nav_target"])
        del st.session_state["nav_target"]

    selected_label = st.radio("Navigation", nav_labels, index=default_nav, label_visibility="collapsed")
    selected_view = nav_keys[nav_labels.index(selected_label)]

    st.markdown("---")
    # Quick Engine Status Check
    from modules.utils import get_ffmpeg_path
    ff_path = get_ffmpeg_path()
    if ff_path:
        st.markdown("<div style='font-size:0.75rem; color:#34D399;'>● FFmpeg Engine: Active</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:0.75rem; color:#FBBF24;'>▲ FFmpeg: Limited to Image Engine</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 0.72rem; color: #64748B; margin-top: 8px;">
        Mathematical Integrity: EVD Strictly Prohibited<br/>
        Power Method: Scratch Iteration
    </div>
    """, unsafe_allow_html=True)

# Page Dispatcher
from views.dashboard import render_dashboard
from views.image_compressor import render_image_compressor
from views.video_compressor import render_video_compressor
from views.target_size import render_target_size
from views.power_method_lab import render_power_method_lab
from views.comparison import render_comparison
from views.analytics import render_analytics
from views.settings import render_settings
from views.about import render_about

if selected_view == "Dashboard":
    render_dashboard()
elif selected_view == "Image Compressor":
    render_image_compressor()
elif selected_view == "Video Compressor":
    render_video_compressor()
elif selected_view == "Target Size Compressor":
    render_target_size()
elif selected_view == "Power Method Lab":
    render_power_method_lab()
elif selected_view == "Compression Comparison":
    render_comparison()
elif selected_view == "Analytics":
    render_analytics()
elif selected_view == "Settings":
    render_settings()
elif selected_view == "About":
    render_about()
