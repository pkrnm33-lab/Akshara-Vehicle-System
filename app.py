import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. BRANDING & CONFIG ---
# Direct reference to your uploaded logo
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

# --- 3. OFFICIAL BRANDED STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    
    /* Branded Header with Logo */
    .branded-header {{
        border-bottom: 4px solid #4CAF50; /* Logo Green Accent */
        padding: 10px 0 20px 0;
        margin-bottom: 30px;
        text-align: center;
    }}
    .logo-img {{ width: 220px; height: auto; }}

    /* Minimalist Metric Cards */
    div[data-testid="stMetric"] {{
        background: #F8F9FA;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}

    /* School Green Primary Buttons */
    div.stButton > button {{
        background-color: #2E7D32; /* Match Logo Green */
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 12px 20px;
        width: 100%;
    }}
    
    /* Logo Yellow for Reset Button */
    .reset-btn button {{ background-color: #FFD700 !important; color: #000000 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SHARED HEADER COMPONENT ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    st.image(LOGO_IMAGE, width=250)
    if title:
        st.markdown(f'<h1 style="color:#000080; font-size:24px;">{title}</h1>', unsafe_allow_html=True)
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
    draw_header()
    with st.container():
        st.subheader("👤 Secure Access")
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

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    c1, c2 = st.columns(2)
    c1.metric("Trip Distance", f"{trip_dist} km")
    c2.metric("Latest Mileage", f"{trip_mileage} km/l")
    
    st.divider()

    st.subheader("1. Daily Update")
    new_odo = st.number_input("Current Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Daily Log"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Updated!"); st.rerun()

    # DIESEL INDICATOR (Triggered at 5.5 mileage)
    if trip_mileage > 5.5:
        st.divider()
        st.success("🎯 TARGET ACHIEVED! READY FOR REFILL.")
        st.subheader("2. Diesel Refilled")
        diesel = st.number_input("Liters Added", min_value=0.0)
        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("Log Fuel & Reset Trip"):
            if diesel > 0:
                supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
