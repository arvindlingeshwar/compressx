"""
Table display utility that avoids pyarrow DLL execution restrictions.
Renders pandas DataFrames and lists of dicts as modern, responsive HTML tables.
"""

import streamlit as st
import pandas as pd
from typing import Union, List, Dict, Any


def render_html_table(data: Union[pd.DataFrame, List[Dict[str, Any]]], height: int = None):
    """
    Renders tabular data as styled HTML without invoking pyarrow.lib.
    """
    if isinstance(data, list):
        if not data:
            st.info("No records to display.")
            return
        df = pd.DataFrame(data)
    else:
        df = data

    if df.empty:
        st.info("No records to display.")
        return

    html_code = df.to_html(index=False, classes="compressx-table", border=0, escape=False)
    
    style = """
    <style>
    .table-container {
        width: 100%;
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin: 10px 0;
        background: rgba(15, 23, 42, 0.6);
    }
    table.compressx-table {
        width: 100%;
        border-collapse: collapse;
        font-family: inherit;
        font-size: 0.88rem;
        color: #F8FAFC;
        text-align: left;
    }
    table.compressx-table th {
        background: rgba(30, 41, 59, 0.85);
        color: #A78BFA;
        font-weight: 700;
        padding: 10px 14px;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        text-transform: uppercase;
        font-size: 0.78rem;
        letter-spacing: 0.05em;
    }
    table.compressx-table td {
        padding: 9px 14px;
        border-bottom: 1px solid rgba(51, 65, 85, 0.5);
        color: #E2E8F0;
    }
    table.compressx-table tr:hover {
        background: rgba(99, 102, 241, 0.1);
    }
    table.compressx-table tr:last-child td {
        border-bottom: none;
    }
    </style>
    """
    st.markdown(f"{style}<div class='table-container'>{html_code}</div>", unsafe_allow_html=True)
