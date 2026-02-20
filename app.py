import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. BRANDING & LOGO CONFIG ---
# This matches the file you uploaded to GitHub
LOGO_IMAGE = "1000000180.jpg" 

st.set_page_config(page_title="Akshara Fleet Portal", page_icon="🚌")

# --- 2. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Ensure Streamlit Secrets are set.")
    st.stop()

# --- 3. HIGH-VISIBILITY BRANDED STYLING ---
st.markdown(f"""
    <style>
    /* Force white background for the entire app */
    .stApp {{ background-color: #FFFFFF !important; }}
    
    /* Force all text to be Dark Navy for readability */
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000080 !important; 
    }}

    /* Branded Header with Logo */
    .branded-header {{
        border-bottom: 4px solid #4CAF50; /* Logo Green Accent */
        padding: 10px 0 20px 0;
        margin-bottom: 30px;
        text-align: center;
    }}
    .logo-img {{ width: 220px; height: auto; }}

    /* FIXED METRIC CARDS: Forced dark text on light gray */
    div[data-testid="stMetric"] {{
        background: #F0F2F6 !important;
        border: 2px solid #E0E0E0 !important;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    /* Force metric label and value colors specifically */
    div[data-testid="stMetricLabel"] > div {{ color: #444444 !important; font-weight: 600 !important; }}
    div[data-testid="stMetricValue"] > div {{ color: #000080 !important; font-weight: 800 !important; }}

    /* Inputs: Force dark text inside input boxes */
    input {{
        color: #000000 !important;
        background-color: #F8F9FA !important;
    }}

    /* School Green Primary Buttons */
    div.stButton > button {{
        background-color: #2E7D32 !important; /* Match Logo Green */
        color: #FFFFFF !important;
        border-radius: 8px;
        font-weight: 700;
        border: none;
        padding: 12px 20px;
        width: 100%;
    }}
    
    /* Logo Yellow for Reset Button */
    .reset-btn button {{ 
        background-color: #FFD700 !important; 
        color: #000000 !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SHARED HEADER COMPONENT ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    try:
        st.image(LOGO_IMAGE, width=250)
    except:
        st.markdown('<h1 style="color:#000080;">AKSHARA PUBLIC SCHOOL</h1>', unsafe_allow_html=True)
    if title:
        st.markdown(f'<h2 style="color:#000080; font-size:24px;">{title}</h2>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. DATA LOADER ---
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 6. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    draw_header("FLEET LOGIN")
    with st.container():
        user_input = st.text_input("Username").upper().strip()
        
        if user_input == "MANAGER":
            password = st.text_input("Password", type="password")
            if st.button("Login as Manager"):
                if password == "Akshara@2026": 
                    st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
                else: st.error("Invalid Password")
        else:
            if st.button("Login as Driver"):
                if not df.empty and user_input in df['driver'].str.upper().str.strip().values:
                    st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
                else: st.warning("Driver not found.")
    st.stop()

# --- 7. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    draw_header("🏆 MANAGER PORTAL")
    t1, t2, t3 = st.tabs(["📊 Performance", "➕ Add Vehicle", "⚙️ Admin"])
    
    with t1:
        if not df.empty:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']], use_container_width=True, hide_index=True)
            st.download_button("📥 Export CSV", data=m_df.to_csv(index=False), file_name="akshara_fleet.csv")

    with t2:
        st.subheader("Enroll New Bus")
        p_n = st.text_input("Plate Number").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("Vehicle Enrolled!")
            st.rerun()

    with t3:
        if not df.empty:
            target = st.selectbox("Remove Vehicle", df['plate'].unique())
            if st.button(f"Delete {target}"):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.rerun()

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    # VISIBLE METRIC CARDS
    c1, c2 = st.columns(2)
    c1.metric("Trip Distance", f"{trip_dist} km")
    c2.metric("Efficiency", f"{trip_mileage} km/l")
    
    st.divider()

    st.subheader("1. Update Daily Reading")
    new_odo = st.number_input("Current Odometer", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Log"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Reading Saved!"); st.rerun()

    # DIESEL INDICATOR (Only shows if Mileage > 5.5)
    if trip_mileage > 5.5:
        st.divider()
        st.success("🎯 TARGET MET! READY FOR DIESEL LOG.")
        st.subheader("2. Diesel Refilled")
        diesel = st.number_input("Liters Added", min_value=0.0)
        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("Log Fuel & Start New Trip"):
            if diesel > 0:
                supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
