import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. BRANDING & LOGO ---
LOGO_IMAGE = "1000000180.jpg" 

st.set_page_config(page_title="Akshara Fleet Portal", page_icon="🚌")

# --- 2. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Check Streamlit Secrets.")
    st.stop()

# --- 3. HIGH-VISIBILITY DARK STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117 !important; }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: #FFFFFF !important; }}

    .branded-header {{
        border-bottom: 4px solid #4CAF50;
        padding: 10px 0 20px 0;
        margin-bottom: 30px;
        text-align: center;
        background-color: #1A1C24;
    }}

    div[data-testid="stMetric"] {{
        background: #1A1C24 !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 12px;
        padding: 15px;
    }}
    div[data-testid="stMetricLabel"] > div {{ color: #BBBBBB !important; }}
    div[data-testid="stMetricValue"] > div {{ color: #FFFFFF !important; font-weight: 800 !important; }}

    input {{
        color: #FFFFFF !important;
        background-color: #262730 !important;
        border: 1px solid #4CAF50 !important;
    }}

    div.stButton > button {{
        background-color: #2E7D32 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        font-weight: 700;
        border: none;
        padding: 12px 20px;
        width: 100%;
    }}
    
    .reset-btn button, .delete-btn button {{ 
        background-color: #FFD700 !important; 
        color: #000000 !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA LOADER ---
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 5. SHARED HEADER ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    try:
        st.image(LOGO_IMAGE, width=250)
    except:
        st.markdown('<h1 style="color:#FFFFFF;">AKSHARA PUBLIC SCHOOL</h1>', unsafe_allow_html=True)
    if title:
        st.markdown(f'<h2 style="color:#4CAF50; font-size:22px;">{title}</h2>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. LOGIN GATE ---
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

# --- 7. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    draw_header("🏆 MANAGER PORTAL")
    t1, t2, t3 = st.tabs(["📊 Performance", "➕ Add Vehicle", "⚙️ Admin"])
    
    with t1:
        if not df.empty:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            # Mileage is still calculated for your info
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            # Added dedicated Diesel Column
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'fuel_liters', 'Mileage']].rename(columns={'fuel_liters': 'Diesel (Ltrs)'}), 
                         use_container_width=True, hide_index=True)
            st.download_button("📥 Export CSV", data=m_df.to_csv(index=False), file_name="fleet_report.csv")

    with t2:
        st.subheader("Enroll New Vehicle")
        p_n = st.text_input("Plate Number").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save to System"):
            if p_n and d_n:
                supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
                st.success(f"Vehicle {p_n} added!")
                st.rerun()

    with t3:
        st.subheader("Remove Vehicle")
        if not df.empty:
            target = st.selectbox("Select Vehicle to Delete", df['plate'].unique())
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if st.button(f"Permanently Remove {target}"):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 8. DRIVER INTERFACE ---
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
    if st.button("Save Reading"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer Updated!"); st.rerun()

    # DIESEL SECTION IS NOW ALWAYS VISIBLE
    st.divider()
    st.subheader("2. Diesel Refilled")
    diesel = st.number_input("Liters Added", min_value=0.0)
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Log Fuel & Reset Trip"):
        if diesel > 0:
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            st.success("Fuel Logged!")
            st.rerun()
        else:
            st.error("Please enter the number of liters.")
    st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
