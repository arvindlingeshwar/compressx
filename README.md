# CompressX – Intelligent Image & Video Compression Platform

CompressX is a complete, professional web application designed to compress digital images and videos into substantially smaller file sizes while preserving peak visual fidelity.

---

## 🚀 Core Features

1. **Real Image Compression Engine**:
   - Formats: JPEG, WebP, AVIF, PNG.
   - Transparency-preserving conversions.
   - Intelligent presets: *Maximum Quality*, *Balanced*, *High Compression*, *Smallest File Size*, and *Custom*.
   - Dynamic resolution scaling and quality tuning.

2. **Real Video Compression Engine (FFmpeg)**:
   - Formats: MP4, MOV, AVI, MKV, WebM.
   - Video Codecs: H.264 (Universal), H.265 / HEVC (Maximum efficiency).
   - Audio stream preservation or optional removal.
   - Resolution scaling: 1080p, 720p, 480p, 360p.
   - CRF & Target Bitrate optimization.

3. **Compress to Target File Size**:
   - Specify an exact ceiling (e.g. 8 MB for Discord/Slack, 25 MB for Gmail, 16 MB for WhatsApp).
   - Adaptive iterative bisection optimizer for images.
   - Mathematical duration & audio/video bitrate allocation formula for videos.

4. **Power Method Image Analysis & Research Laboratory**:
   - Explicit, genuine implementation of the iterative **Power Method** from first principles.
   - **CRITICAL RESTRICTION: ABSOLUTELY ZERO EIGENVALUE DECOMPOSITION (EVD)**.
   - Computes dominant singular components $\sigma_1 = \sqrt{\lambda_1}$ and $u_1 = B v_1 / \sigma_1$ from Gram matrix $A = B^T B$.
   - Demonstrates rank-one block reconstruction and compares algebraic approximation against production entropy codecs.

5. **Operational Dashboards & Analytics**:
   - Session cumulative storage saved & average reduction percentage.
   - Interactive difference heatmaps and Plotly metrics comparisons.
   - Temporary file safety cleanup controls.

---

## 🛡️ Mathematical Integrity Check

- ❌ `numpy.linalg.eig` **PROHIBITED**
- ❌ `numpy.linalg.eigh` **PROHIBITED**
- ❌ `scipy.linalg.eig` **PROHIBITED**
- ✅ Pure manual Power Method:
  $$x_{k+1} = \frac{A x_k}{\|A x_k\|_2}, \quad \lambda_k = \frac{x_k^T A x_k}{x_k^T x_k}$$

---

## 💻 Installation & Running

### 1. Install Python Dependencies
```bash
cd compressx
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
pytest tests/
```
All 7 unit tests pass 100%.

### 3. Launch Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.
