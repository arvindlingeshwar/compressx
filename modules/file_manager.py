"""
Session File Management and History Tracker for CompressX.
Handles session temporary storage, ZIP compilation, and history cleanup.
"""

import os
import zipfile
import io
from typing import List, Dict, Any, Optional


def create_zip_archive(files_dict: Dict[str, bytes]) -> bytes:
    """
    Creates a ZIP archive in memory from a dict of {filename: bytes}.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for fname, data in files_dict.items():
            zip_file.writestr(fname, data)
    return buffer.getvalue()


def record_history(session_state, item: Dict[str, Any]):
    """Appends processed task record to session history."""
    if "compression_history" not in session_state:
        session_state["compression_history"] = []
    session_state["compression_history"].append(item)


def get_session_stats(session_state) -> Dict[str, Any]:
    """Computes session-wide totals."""
    history = session_state.get("compression_history", [])
    total_files = len(history)
    orig_total = sum(item.get("original_size", 0) for item in history)
    comp_total = sum(item.get("compressed_size", 0) for item in history)
    saved_total = max(0, orig_total - comp_total)
    avg_reduction = (saved_total / orig_total * 100.0) if orig_total > 0 else 0.0

    return {
        "total_files": total_files,
        "original_bytes": orig_total,
        "compressed_bytes": comp_total,
        "saved_bytes": saved_total,
        "avg_reduction_pct": avg_reduction
    }
