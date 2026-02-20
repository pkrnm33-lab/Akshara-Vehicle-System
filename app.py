import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. BRANDING & LOGO CONFIG ---
LOGO_IMAGE = "1000000180.jpg" 

st.set_page_config(page_title="Akshara Fleet Portal", page_icon="🚌")

# --- 2. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error.")
    st.stop()

# --- 3. HIGH-CONTRAST DARK STYLING ---
st.markdown(f"""
    <style>
    /* Deep charcoal background for the entire app */
    .stApp {{ background-color: #0E1117 !important; }}
    
    /* Force all text to be bright white or neon for readability */
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #FFFFFF !important; 
    }}

    /* Branded Header with Logo */
    .branded-header {{
        border-bottom: 4px solid #4CAF50; /* Logo Green Accent */
        padding: 10px 0 20px 0;
        margin-bottom: 30px;
        text-align: center;
        background-color: #1A1C24;
    }}

    /* DARK METRIC CARDS: Neon text on dark background */
    div[data-testid="stMetric"] {{
        background: #1A1C24 !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 10px rgba(0,255,0,0.1);
    }}
    /* Force neon colors for values */
    div[data-testid="stMetricLabel"] > div {{ color: #BBBBBB !important; }}
    div[data-testid="stMetricValue"] > div {{ color: #39FF14 !important; font-weight: 800 !important; }}

    /* Inputs: Light text on dark boxes */
    input {{
        color: #FFFFFF !important;
        background-color: #262730 !important;
        border: 1px solid #4CAF50 !important;
    }}

    /* School Green Primary Buttons */
    div.stButton > button {{
        background-color: #2E7D32 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        font-weight: 700;
        border: none;
        padding: 12px 20px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(46,125,50,0.3);
    }}
    
    /* Logo Yellow for Reset Button */
    .reset-btn button {{ 
        background-color: #FFD700 !important; 
        color: #000000 !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SHARED HEADER ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    try:
        st.image(LOGO_IMAGE, width=250)
    except:
        st.markdown('<h1 style="color:#FFFFFF;">AKSHARA PUBLIC SCHOOL</h1>', unsafe_allow_html=True)
    if title:
        st.markdown(f'<h2 style="color:#4CAF50; font-size:24px;">{title}</h2>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. DATA ---
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 6. LOGIN ---
if 'logged_in' not in st.session_state:
    draw_header("FLEET LOGIN")
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

# --- 7. MANAGER ---
if st.session_state.role == "manager":
    draw_header("🏆 MANAGER PORTAL")
    t1, t2, t3 = st.tabs(["📊 Performance", "➕ Add Vehicle", "⚙️ Admin"])
    with t1:
        if not df.empty:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']], use_container_width=True, hide_index=True)

# --- 8. DRIVER ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    c1, c2 = st.columns(2)
    c1.metric("Trip Distance", f"{trip_dist} km")
    c2.metric("Efficiency", f"{trip_mileage} km/l")
    
    st.divider()
    st.subheader("1. Update Daily Reading")
    new_odo = st.number_input("Current Odometer", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Log"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Reading Saved!"); st.rerun()

    if trip_mileage > 5.5:
        st.divider()
        st.success("🎯 TARGET MET!")
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
