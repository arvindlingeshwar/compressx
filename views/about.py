"""
CompressX - About and Mathematical Audit Page.
"""

import streamlit as st


def render_about():
    st.markdown("## ℹ️ About CompressX")
    st.markdown("""
    **CompressX** is an intelligent multimedia compression platform combining modern web codecs 
    (WebP, AVIF, H.264/HEVC via FFmpeg) with an explicit Numerical Methods Power Method research laboratory.
    
    **Lead Developer & Research Author:** **Aravind L**
    """)

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🛡️ Mathematical Restriction Compliance")
        st.info("""
        **EIGENVALUE DECOMPOSITION (EVD) IS STRICTLY PROHIBITED:**
        - ❌ `numpy.linalg.eig` is never used.
        - ❌ `numpy.linalg.eigh` is never used.
        - ❌ `scipy.linalg.eig` is never used.
        - ✅ Power Method is implemented purely from scratch via:
          $y = Ax, \\quad x_{k+1} = \\frac{y}{\\|y\\|}, \\quad \\lambda_k = \\frac{x_k^T A x_k}{x_k^T x_k}$
        - ✅ Dominant singular components are derived from $A = B^T B$.
        """)

    with c2:
        st.markdown("### 🚀 Real-World Problem Solved")
        st.success("""
        - **Upload Limits:** Compress files to under 8 MB / 25 MB for Discord, WhatsApp, Gmail.
        - **Bandwidth Reduction:** Save up to 70-90% data on mobile networks.
        - **Lossless & Lossy:** Support for transparency-preserving WebP, PNG, and high-efficiency HEVC.
        """)
