"""
CompressX - Compression Analytics Dashboard.
"""

import streamlit as st
import pandas as pd
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
from modules.file_manager import get_session_stats
from modules.utils import format_bytes
from modules.table_view import render_html_table


def render_analytics():
    st.markdown("## 📊 Compression Analytics")

    history = st.session_state.get("compression_history", [])
    if not history:
        st.info("No processing history available yet. Compress an image or video to populate analytics.")
        return

    stats = get_session_stats(st.session_state)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jobs", stats["total_files"])
    m2.metric("Cumulative Space Saved", format_bytes(stats["saved_bytes"]))
    m3.metric("Average Reduction", f"{stats['avg_reduction_pct']:.1f}%")
    avg_speed = (sum(h.get("processing_time", 0) for h in history) / len(history)) if history else 0
    m4.metric("Avg Latency", f"{avg_speed:.2f}s")

    st.markdown("---")

    df = pd.DataFrame(history)

    c1, c2 = st.columns(2)
    with c1:
        # File size comparison
        chart_df = df.copy()
        chart_df["Original MB"] = chart_df["original_size"] / (1024 * 1024)
        chart_df["Compressed MB"] = chart_df["compressed_size"] / (1024 * 1024)

        if HAS_PLOTLY:
            fig_bar = px.bar(
                chart_df,
                x="name",
                y=["Original MB", "Compressed MB"],
                barmode="group",
                title="File Size Comparison (MB)",
                color_discrete_sequence=["#38BDF8", "#818CF8"]
            )
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.4)",
                plot_bgcolor="rgba(30, 41, 59, 0.3)",
                height=300,
                margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.markdown("#### File Size Comparison (MB)")
            st.bar_chart(chart_df.set_index("name")[["Original MB", "Compressed MB"]])

    with c2:
        if HAS_PLOTLY:
            fig_pie = px.pie(
                df,
                names="name",
                values="reduction_pct",
                title="Percentage Reduction by Item",
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig_pie.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.4)",
                plot_bgcolor="rgba(30, 41, 59, 0.3)",
                height=300,
                margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.markdown("#### Reduction Percentage by Item (%)")
            st.bar_chart(df.set_index("name")["reduction_pct"])

    st.markdown("### 📋 Full Job Log")
    log_display = []
    for h in history:
        log_display.append({
            "Type": h.get("type", "Media"),
            "Filename": h.get("name", "Unknown"),
            "Original Size": format_bytes(h.get("original_size", 0)),
            "Compressed Size": format_bytes(h.get("compressed_size", 0)),
            "Reduction": f"{h.get('reduction_pct', 0.0):.1f}%",
            "Ratio": f"{h.get('compression_ratio', 1.0):.2f}x",
            "Compute Time": f"{h.get('processing_time', 0.0):.2f}s"
        })
    render_html_table(log_display)

    csv_data = pd.DataFrame(log_display).to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Analytics CSV", data=csv_data, file_name="compressx_analytics.csv", mime="text/csv")
