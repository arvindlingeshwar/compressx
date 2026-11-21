"""
CompressX - Power Method Image Analysis & Compression Research Module.
Pure numerical implementation from scratch.
STRICT RULE: NO EIGENVALUE DECOMPOSITION (EVD) IS USED.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from modules.power_method import power_method
from modules.power_method_image import block_power_method_approximation
from modules.image_compressor import compress_image
from modules.utils import format_bytes
from modules.table_view import render_html_table


def render_power_method_lab():
    st.markdown("## 🧮 Power Method Research Laboratory")
    st.markdown("""
    Explore the explicit numerical mechanics of the **Power Method** applied to image blocks:
    $A = B^T B, \\quad x_{k+1} = \\frac{A x_k}{\\|A x_k\\|}, \\quad \\lambda_k = \\frac{x_k^T A x_k}{x_k^T x_k}$
    **STRICT COMPLIANCE:** Zero Eigenvalue Decomposition (`np.linalg.eig` or `scipy`) functions are used.
    """)

    tabs = st.tabs(["1. Matrix Numerical Lab", "2. Rank-1 Block Image Approximation", "3. Numerical vs Codec Benchmark"])

    with tabs[0]:
        st.markdown("### 🎛️ Interactive Matrix Power Method")
        col_m1, col_m2 = st.columns([1, 1.3])

        with col_m1:
            choice = st.selectbox("Select Test Matrix:", ["2×2 Known Symmetric (λ=4.0)", "3×3 Positive Semidefinite (λ=12.0)", "Custom"])
            mat_str = "3.0, 1.0\n1.0, 3.0"
            if "3×3" in choice:
                mat_str = "12.0, 0.0, 0.0\n0.0, 7.0, 0.0\n0.0, 0.0, 3.0"

            mat_in = st.text_area("Matrix A entries (rows on newlines):", value=mat_str, height=100)
            rows = [list(map(float, line.replace(",", " ").split())) for line in mat_in.strip().split("\n") if line.strip()]
            A = np.array(rows, dtype=float)

            max_iter = st.slider("Max Iterations:", 5, 100, 35)
            tol = st.selectbox("Tolerance:", [1e-4, 1e-6, 1e-8], index=1)
            run_pm = st.button("Calculate Dominant Eigenpair", type="primary", use_container_width=True)

        with col_m2:
            res_pm = power_method(A, max_iter=max_iter, tol=tol)
            st.metric("Dominant Eigenvalue (λ₁)", f"{res_pm['dominant_eigenvalue']:.6f}")
            st.code(f"Dominant Eigenvector v₁: {np.round(res_pm['dominant_eigenvector'], 5).tolist()}", language="python")

            # Convergence graph
            history = res_pm["history"]
            iters = [h["iteration"] for h in history]
            evals = [h["eigenvalue"] for h in history]
            errs = [max(1e-15, h["error"]) for h in history]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=iters, y=evals, mode="lines+markers", name="λ Estimate", line=dict(color="#8B5CF6", width=2)))
            fig.update_layout(
                title="Rayleigh Quotient Convergence per Iteration",
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.4)",
                plot_bgcolor="rgba(30, 41, 59, 0.3)",
                height=240,
                margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.markdown("### 🖼️ Rank-1 Dominant Component Reconstruction")
        st.write("Constructs $A = B^T B$ for each block, extracts dominant eigenpair $(\\lambda_1, v_1)$, computes $\\sigma_1 = \\sqrt{\\lambda_1}$ and $u_1 = B v_1 / \\sigma_1$, and forms rank-1 block $B_1 = \\sigma_1 u_1 v_1^T$.")

        # Create benchmark test matrix
        b_size = st.select_slider("Sub-Block Size (B×B):", [4, 8, 16], value=8)

        # Generate smooth test pattern
        size = 128
        y, x = np.ogrid[:size, :size]
        test_img = (128.0 + 127.0 * np.sin(x / 8.0) * np.cos(y / 8.0)).astype(np.uint8)

        pm_res = block_power_method_approximation(test_img, block_size=b_size, max_iter=25)

        c_orig, c_recon = st.columns(2)
        with c_orig:
            st.image(test_img, caption="Original Pattern Matrix (128×128)", use_container_width=True)
        with c_recon:
            st.image(pm_res["reconstructed_image"], caption=f"Rank-1 Power Method Reconstructed (PSNR: {pm_res['psnr']:.2f} dB)", use_container_width=True)

        st.info(f"Numerical Blocks: {pm_res['num_blocks']} | Encoded components: {format_bytes(pm_res['encoded_bytes'])} | Theoretical Compression Ratio: {pm_res['compression_ratio']:.2f}x")

    with tabs[2]:
        st.markdown("### ⚖️ Numerical Approximation vs Production Codecs")
        st.markdown("""
        The Power Method is an **algebraic matrix approximation technique** for low-rank modeling. 
        Below is a comparison showing why production applications utilize transform codecs (WebP, AVIF) for file storage, 
        while the Power Method is used for spectral orientation analysis.
        """)

        from PIL import Image
        pil_test = Image.fromarray(test_img)
        webp_res = compress_image(pil_test, output_format="WEBP", quality=80)

        comp_table = pd.DataFrame([
            {
                "Technique": "Power Method Rank-1 (Numerical)",
                "Nature": "Iterative Spectral Decomposition (No EVD)",
                "PSNR Quality": f"{pm_res['psnr']:.2f} dB",
                "Storage Model": "Float32 singular components (σ₁, u₁, v₁)",
                "Practical Use": "Mathematical analysis, feature extraction, low-rank approximation"
            },
            {
                "Technique": "WebP Codec (Production)",
                "Nature": "DCT Transform + Arithmetic Entropy Coding",
                "PSNR Quality": f"{webp_res['psnr']:.2f} dB",
                "Storage Model": f"{format_bytes(webp_res['size_bytes'])} bitstream file",
                "Practical Use": "Real-world web and mobile image transmission"
            }
        ])
        render_html_table(comp_table)
