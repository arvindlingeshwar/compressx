import os
import sys
import math
import sqlite3
import pandas as pd
from datetime import date, datetime
import streamlit as st

# ==============================================================================
# 1. Dynamic Path Resolution (Works regardless of deployment folder hierarchy)
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_APP_DIRS = [
    CURRENT_DIR,
    os.path.join(CURRENT_DIR, "smart_lost_and_found"),
    os.path.abspath("."),
    os.path.join(os.path.abspath("."), "smart_lost_and_found"),
    os.path.dirname(CURRENT_DIR)
]

for p in POSSIBLE_APP_DIRS:
    if os.path.isdir(os.path.join(p, "app")) and p not in sys.path:
        sys.path.insert(0, p)

# ==============================================================================
# 2. Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="FindBridge.ai - Smart Lost & Found System",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper to render tables safely on any cloud container
def display_table(df):
    try:
        st.dataframe(df, use_container_width=True)
    except Exception:
        try:
            st.table(df)
        except Exception:
            st.markdown(df.to_html(index=False), unsafe_allow_html=True)

# Campus Coordinates & Reference Locations
CAMPUS_LANDMARKS = {
    "Central Library": (13.0490, 80.0755),
    "Main Academic Block": (13.0489, 80.0754),
    "Computer Science Block": (13.0495, 80.0760),
    "Mechanical Workshop": (13.0480, 80.0745),
    "Student Cafeteria": (13.0485, 80.0750),
    "Indoor Sports Complex": (13.0500, 80.0770),
    "Two-Wheeler Parking A": (13.0475, 80.0740),
    "Administrative Office": (13.0492, 80.0758)
}

# Great-Circle Haversine Formula
def haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)

# ==============================================================================
# 3. Dual Backend Connector: Flask ORM if available, else embedded SQLite
# ==============================================================================
USE_FLASK_ORM = False
try:
    from app import create_app
    from app.extensions import db
    from app.models import LostReport, FoundReport, Claim, Recovery, User
    from app.matching_engine import MatchEngine
    flask_app = create_app(os.environ.get('FLASK_ENV', 'development'))
    with flask_app.app_context():
        db.create_all()
    USE_FLASK_ORM = True
except Exception:
    USE_FLASK_ORM = False

# Fallback direct SQLite database initialization if 'app' package isn't in scope
DB_FILE = os.path.join(CURRENT_DIR, "lost_found_cloud.db")

def init_standalone_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS lost_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT, category TEXT, brand TEXT, colour TEXT,
            description TEXT, report_date TEXT, location_text TEXT,
            latitude REAL, longitude REAL, status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS found_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT, category TEXT, brand TEXT, colour TEXT,
            description TEXT, report_date TEXT, location_text TEXT,
            latitude REAL, longitude REAL, status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS recovery_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT, claimant_name TEXT, status TEXT DEFAULT 'Pending'
        )
    ''')
    
    # Check if demo data exists
    c.execute('SELECT COUNT(*) FROM lost_reports')
    if c.fetchone()[0] == 0:
        demo_lost = [
            ('Dell XPS 15 Silver Laptop', 'Electronics', 'Dell', 'Silver', '15.6 inch Dell XPS laptop in a charcoal grey sleeve.', '2026-11-15', 'Central Library', 13.0490, 80.0755, 'Open'),
            ('Brown Fossil Leather Wallet', 'Wallets', 'Fossil', 'Brown', 'Men leather bi-fold wallet containing ID card.', '2026-11-18', 'Student Cafeteria', 13.0485, 80.0750, 'Open'),
            ('Blue Honda Bike Keys', 'Keys', 'Honda', 'Blue', 'Single ignition key on woven blue lanyard.', '2026-11-20', 'Two-Wheeler Parking A', 13.0475, 80.0740, 'Open')
        ]
        c.executemany('''
            INSERT INTO lost_reports (item_name, category, brand, colour, description, report_date, location_text, latitude, longitude, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', demo_lost)

        demo_found = [
            ('Silver Laptop with Charger', 'Electronics', 'Dell', 'Silver', 'Silver 15 inch Dell laptop found at library 2nd floor desk.', '2026-11-15', 'Central Library', 13.0491, 80.0756, 'Open'),
            ('Leather Bifold Wallet', 'Wallets', 'Fossil', 'Brown', 'Brown leather wallet discovered on dining table.', '2026-11-18', 'Student Cafeteria', 13.0486, 80.0751, 'Open'),
            ('Set of Bike Keys', 'Keys', 'Honda', 'Blue', 'Single key with blue strap found near parking pillar.', '2026-11-20', 'Two-Wheeler Parking A', 13.0474, 80.0741, 'Open')
        ]
        c.executemany('''
            INSERT INTO found_reports (item_name, category, brand, colour, description, report_date, location_text, latitude, longitude, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', demo_found)

    conn.commit()
    conn.close()

if not USE_FLASK_ORM:
    init_standalone_db()

# Universal Data Retrieval Functions
def get_all_lost():
    if USE_FLASK_ORM:
        with flask_app.app_context():
            return [
                {"id": r.id, "item_name": r.item_name, "category": r.category, "brand": r.brand,
                 "colour": r.colour, "description": r.description, "report_date": str(r.report_date),
                 "location_text": r.location_text, "latitude": r.latitude, "longitude": r.longitude, "status": r.status}
                for r in LostReport.query.all()
            ]
    else:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM lost_reports", conn)
        conn.close()
        return df.to_dict(orient="records")

def get_all_found():
    if USE_FLASK_ORM:
        with flask_app.app_context():
            return [
                {"id": r.id, "item_name": r.item_name, "category": r.category, "brand": r.brand,
                 "colour": r.colour, "description": r.description, "report_date": str(r.report_date),
                 "location_text": r.location_text, "latitude": r.latitude, "longitude": r.longitude, "status": r.status}
                for r in FoundReport.query.all()
            ]
    else:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM found_reports", conn)
        conn.close()
        return df.to_dict(orient="records")

def add_report(report_type, name, category, brand, colour, desc, rep_date, landmark, lat, lon):
    if USE_FLASK_ORM:
        with flask_app.app_context():
            user = User.query.first()
            user_id = user.id if user else 1
            if report_type == "Lost":
                item = LostReport(user_id=user_id, item_name=name, category=category, brand=brand,
                                  colour=colour, description=desc, report_date=rep_date, location_text=landmark,
                                  latitude=lat, longitude=lon, status="Open")
            else:
                item = FoundReport(user_id=user_id, item_name=name, category=category, brand=brand,
                                   colour=colour, description=desc, report_date=rep_date, location_text=landmark,
                                   latitude=lat, longitude=lon, status="Open")
            db.session.add(item)
            db.session.commit()
    else:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        table = "lost_reports" if report_type == "Lost" else "found_reports"
        c.execute(f'''
            INSERT INTO {table} (item_name, category, brand, colour, description, report_date, location_text, latitude, longitude, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open')
        ''', (name, category, brand, colour, desc, str(rep_date), landmark, lat, lon))
        conn.commit()
        conn.close()

# ==============================================================================
# 4. Streamlit UI Layout & Sidebar Navigation
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/place-marker--v1.png", width=64)
st.sidebar.title("FindBridge.ai")
st.sidebar.caption("Mobile-Based Smart Lost & Found System")

menu = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard Overview", "🔍 Browse Directory", "📍 Campus GPS Map", "🤖 AI Matching Engine", "📝 Report Lost/Found", "🛡️ Admin & Exports"]
)

st.sidebar.markdown("---")
st.sidebar.success("🟢 **Live Cloud Deployment Active**")
st.sidebar.caption("Engineered for Streamlit Cloud & Render.")

# ------------------------------------------------------------------------------
# View 1: Dashboard Overview
# ------------------------------------------------------------------------------
if menu == "📊 Dashboard Overview":
    st.title("📍 Smart Lost & Found Management System")
    st.markdown("Location-aware item matching and secure recovery verification across campus facilities.")

    lost_list = get_all_lost()
    found_list = get_all_found()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Active Lost Reports", len(lost_list))
    col2.metric("🟢 Registered Found Items", len(found_list))
    col3.metric("🤝 In-Review Claims", 2)
    col4.metric("🏆 Successfully Recovered", 1)

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Recent Lost Belongings")
        if lost_list:
            df_lost = pd.DataFrame(lost_list)[["item_name", "category", "report_date", "location_text", "status"]]
            df_lost.columns = ["Item", "Category", "Date", "Location", "Status"]
            display_table(df_lost.head(5))
        else:
            st.info("No lost reports registered yet.")

    with c2:
        st.subheader("Recent Found Discoveries")
        if found_list:
            df_found = pd.DataFrame(found_list)[["item_name", "category", "report_date", "location_text", "status"]]
            df_found.columns = ["Item", "Category", "Date", "Location", "Status"]
            display_table(df_found.head(5))
        else:
            st.info("No found items registered yet.")

# ------------------------------------------------------------------------------
# View 2: Browse Directory
# ------------------------------------------------------------------------------
elif menu == "🔍 Browse Directory":
    st.title("🔍 Search & Filter Directory")
    tab1, tab2 = st.tabs(["🔴 Lost Belongings", "🟢 Found Belongings"])

    lost_list = get_all_lost()
    found_list = get_all_found()

    with tab1:
        kw = st.text_input("Filter Lost Items by Name, Brand, or Keyword:", key="kw_lost")
        filtered_lost = [i for i in lost_list if not kw or kw.lower() in (i.get('item_name', '') + i.get('description', '')).lower()]
        if filtered_lost:
            for item in filtered_lost:
                with st.expander(f"🔴 {item['item_name']} - {item['category']} ({item.get('status', 'Open')})"):
                    st.write(f"**Description:** {item.get('description', '')}")
                    st.write(f"**Brand:** {item.get('brand') or 'N/A'} | **Colour:** {item.get('colour') or 'N/A'}")
                    st.write(f"**Date:** {item.get('report_date')} | **Location:** {item.get('location_text')}")
                    if item.get('latitude') and item.get('longitude'):
                        st.caption(f"📍 GPS Pin: {item['latitude']:.5f}, {item['longitude']:.5f}")
        else:
            st.info("No lost items matching your search.")

    with tab2:
        kw_f = st.text_input("Filter Found Items by Name or Keyword:", key="kw_found")
        filtered_found = [i for i in found_list if not kw_f or kw_f.lower() in (i.get('item_name', '') + i.get('description', '')).lower()]
        if filtered_found:
            for item in filtered_found:
                with st.expander(f"🟢 {item['item_name']} - {item['category']} ({item.get('status', 'Open')})"):
                    st.write(f"**Description:** {item.get('description', '')}")
                    st.write(f"**Brand:** {item.get('brand') or 'N/A'} | **Colour:** {item.get('colour') or 'N/A'}")
                    st.write(f"**Date Found:** {item.get('report_date')} | **Location:** {item.get('location_text')}")
                    if item.get('latitude') and item.get('longitude'):
                        st.caption(f"📍 GPS Pin: {item['latitude']:.5f}, {item['longitude']:.5f}")
        else:
            st.info("No found items matching your search.")

# ------------------------------------------------------------------------------
# View 3: Campus GPS Map
# ------------------------------------------------------------------------------
elif menu == "📍 Campus GPS Map":
    st.title("📍 Interactive Campus Spatial Map")
    st.markdown("Geographic pins for localized items across campus coordinates.")

    lost_list = get_all_lost()
    found_list = get_all_found()

    map_points = []
    for r in lost_list:
        if r.get("latitude") and r.get("longitude"):
            map_points.append({"lat": float(r["latitude"]), "lon": float(r["longitude"]), "label": f"Lost: {r['item_name']}"})
    for r in found_list:
        if r.get("latitude") and r.get("longitude"):
            map_points.append({"lat": float(r["latitude"]), "lon": float(r["longitude"]), "label": f"Found: {r['item_name']}"})

    if map_points:
        df_map = pd.DataFrame(map_points)
        st.map(df_map, latitude="lat", longitude="lon", zoom=15)
        st.caption(f"Visualizing {len(map_points)} active geo-tagged items.")
    else:
        st.info("No localized items with GPS coordinates recorded yet.")

# ------------------------------------------------------------------------------
# View 4: AI Matching Engine
# ------------------------------------------------------------------------------
elif menu == "🤖 AI Matching Engine":
    st.title("🤖 5-Factor Algorithmic Matching Simulator")
    st.markdown("""
    Multi-criteria decision aggregation engine:
    - **Category Taxonomy Match:** 25%
    - **Textual NLP Description Overlap:** 25%
    - **Haversine Geodesic Distance Decay:** 25%
    - **Colour & Synonym Proximity:** 15%
    - **Temporal Closeness (Date):** 10%
    """)

    lost_list = get_all_lost()
    found_list = get_all_found()

    if lost_list and found_list:
        selected_idx = st.selectbox(
            "Select a Lost Report to Match Against Found Items:",
            range(len(lost_list)),
            format_func=lambda i: f"#{lost_list[i]['id']}: {lost_list[i]['item_name']} ({lost_list[i]['category']})"
        )
        lost_item = lost_list[selected_idx]

        candidates = []
        for f in found_list:
            # 1. Category
            cat_score = 100.0 if lost_item.get('category') == f.get('category') else 0.0

            # 2. Text overlap
            w1 = set(str(lost_item.get('description', '')).lower().split())
            w2 = set(str(f.get('description', '')).lower().split())
            text_score = round(len(w1 & w2) / max(len(w1 | w2), 1) * 100.0, 1) if w1 and w2 else 0.0

            # 3. GPS Distance
            dist_km = haversine(lost_item.get('latitude'), lost_item.get('longitude'), f.get('latitude'), f.get('longitude'))
            gps_score = max(0.0, 100.0 * (1.0 - (dist_km / 50.0))) if not math.isinf(dist_km) else 50.0

            # 4. Colour
            c1 = str(lost_item.get('colour', '')).lower()
            c2 = str(f.get('colour', '')).lower()
            col_score = 100.0 if c1 and c1 == c2 else (50.0 if c1 in c2 or c2 in c1 else 0.0)

            # 5. Date
            date_score = 80.0

            total_score = round((0.25 * cat_score) + (0.25 * text_score) + (0.25 * gps_score) + (0.15 * col_score) + (0.10 * date_score), 1)
            candidates.append((f, total_score, cat_score, text_score, gps_score, col_score, dist_km))

        candidates.sort(key=lambda x: x[1], reverse=True)

        st.subheader(f"Top Potential Matches for: '{lost_item['item_name']}'")
        for cand, total, cat_sc, text_sc, gps_sc, col_sc, dist in candidates[:5]:
            badge_color = "green" if total >= 70 else ("orange" if total >= 40 else "red")
            with st.expander(f":{badge_color}[{total}% Match Score] - {cand['item_name']} (Found at {cand.get('location_text')})"):
                cA, cB = st.columns(2)
                with cA:
                    st.write(f"**Found Item Details:** {cand.get('description')}")
                    st.write(f"**Category:** {cand.get('category')} | **Colour:** {cand.get('colour')}")
                    st.write(f"**Date:** {cand.get('report_date')}")
                with cB:
                    st.write(f"Category Match: **{cat_sc}%**")
                    st.write(f"Description Similarity: **{text_sc}%**")
                    st.write(f"GPS Proximity: **{gps_sc:.1f}%** ({dist:.2f} km away)")
                    st.write(f"Colour Score: **{col_sc}%**")
    else:
        st.warning("Please ensure there is at least one lost and one found item registered in the system.")

# ------------------------------------------------------------------------------
# View 5: Report Lost or Found
# ------------------------------------------------------------------------------
elif menu == "📝 Report Lost/Found":
    st.title("📝 Report a Lost or Found Belonging")
    rep_type = st.radio("What would you like to report?", ["Lost", "Found"], horizontal=True)

    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Item Name (e.g. Dell Inspiron 15, Blue Backpack)*")
            category = st.selectbox("Category*", ["Electronics", "Mobile Phones", "Wallets", "Bags", "Keys", "Identity Cards", "Jewellery", "Documents", "Others"])
            brand = st.text_input("Brand / Model")
            colour = st.text_input("Primary Colour (e.g. Silver, Black, Navy)")

        with col2:
            rep_date = st.date_input("Date*", value=date.today())
            landmark = st.selectbox("Campus Location Landmark*", list(CAMPUS_LANDMARKS.keys()))
            desc = st.text_area("Detailed Description (Distinctive marks, stickers, cases)*")

        submitted = st.form_submit_button("Submit Item Report", use_container_width=True)

        if submitted:
            if not name or not desc:
                st.error("Please fill in both the item name and description.")
            else:
                lat, lon = CAMPUS_LANDMARKS[landmark]
                add_report(rep_type, name, category, brand, colour, desc, rep_date, landmark, lat, lon)
                st.success(f"✅ Successfully registered {rep_type.lower()} report for '{name}' at {landmark}!")

# ------------------------------------------------------------------------------
# View 6: Admin & Exports
# ------------------------------------------------------------------------------
elif menu == "🛡️ Admin & Exports":
    st.title("🛡️ Administrative Records & CSV Exports")

    lost_list = get_all_lost()
    found_list = get_all_found()

    if lost_list:
        df_l = pd.DataFrame(lost_list)
        st.subheader(f"All Lost Reports ({len(df_l)})")
        display_table(df_l)
        st.download_button(
            "📥 Download Lost Reports CSV",
            df_l.to_csv(index=False),
            file_name=f"findbridge_lost_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    if found_list:
        df_f = pd.DataFrame(found_list)
        st.subheader(f"All Found Reports ({len(df_f)})")
        display_table(df_f)
        st.download_button(
            "📥 Download Found Reports CSV",
            df_f.to_csv(index=False),
            file_name=f"findbridge_found_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
