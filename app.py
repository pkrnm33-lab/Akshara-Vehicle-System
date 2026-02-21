import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

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

# --- 3. STYLING (DARK THEME) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117 !important; }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: #FFFFFF !important; }}
    .branded-header {{ border-bottom: 4px solid #4CAF50; padding: 10px 0 20px 0; margin-bottom: 30px; text-align: center; background-color: #1A1C24; }}
    div[data-testid="stMetricValue"] > div {{ color: #39FF14 !important; font-weight: 800 !important; }}
    div.stButton > button {{ background-color: #2E7D32 !important; color: #FFFFFF !important; border-radius: 8px; font-weight: 700; padding: 12px 20px; width: 100%; }}
    .total-card {{ background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #FFD700; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA LOADER (PROTECTED AGAINST KEYERRORS) ---
def load_data():
    # Forced structures to prevent crashes after reset
    EMPTY_V = pd.DataFrame(columns=['plate', 'driver', 'odo', 'trip_km', 'fuel_liters'])
    EMPTY_F = pd.DataFrame(columns=['id', 'created_at', 'plate', 'driver', 'liters', 'price'])
    EMPTY_M = pd.DataFrame(columns=['id', 'created_at', 'plate', 'service_type', 'cost', 'service_date'])
    try:
        v_res = supabase.table("vehicles").select("*").execute()
        v_df = pd.DataFrame(v_res.data) if v_res.data else EMPTY_V
        f_res = supabase.table("fuel_logs").select("*").execute()
        f_df = pd.DataFrame(f_res.data) if f_res.data else EMPTY_F
        if not f_df.empty: f_df['created_at'] = pd.to_datetime(f_df['created_at'])
        m_res = supabase.table("maintenance_logs").select("*").execute()
        m_df = pd.DataFrame(m_res.data) if m_res.data else EMPTY_M
        return v_df, f_df, m_df
    except: return EMPTY_V, EMPTY_F, EMPTY_M

df_v, df_f, df_m = load_data()

# --- 5. SHARED HEADER ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    try: st.image(LOGO_IMAGE, width=250)
    except: st.markdown('<h1 style="color:#FFFFFF;">AKSHARA PUBLIC SCHOOL</h1>', unsafe_allow_html=True)
    if title: st.markdown(f'<h2 style="color:#4CAF50; font-size:22px;">{title}</h2>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. LOGIN ---
if 'logged_in' not in st.session_state:
    draw_header("FLEET LOGIN")
    user_input = st.text_input("Username").upper().strip()
    if user_input == "MANAGER":
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == "Akshara@2026": 
                st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
            else: st.error("Wrong Password")
    else:
        if st.button("Login as Driver"):
            if not df_v.empty and user_input in df_v['driver'].str.upper().str.strip().values:
                st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
            else: st.warning("Driver not found.")
    st.stop()

# --- 7. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    draw_header("🏆 MANAGER PORTAL")
    t1, t2, t3 = st.tabs(["📊 Performance", "🛠️ Maintenance", "⚙️ Admin Reset"])
    with t1:
        if not df_v.empty:
            report = df_v.copy()
            report['Trip KM'] = report['odo'] - report['trip_km']
            report['Mileage'] = report.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            st.write("### 🚌 Current Trip Performance")
            st.dataframe(report[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']], use_container_width=True, hide_index=True)

# --- 8. DRIVER INTERFACE (FIXED: ADDED MILEAGE HISTORY) ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df_v[df_v['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # 1. LIVE PERFORMANCE METRICS
    trip_d = v_data['odo'] - v_data['trip_km']
    trip_m = round(trip_d / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    c1, c2 = st.columns(2)
    c1.metric("Trip Distance", f"{trip_d} km")
    c2.metric("Current Efficiency", f"{trip_m} km/l")
    
    # 2. NEW: PERFORMANCE HISTORY TABLE
    st.divider()
    st.write("### 📜 Your Performance History")
    if not df_f.empty and v_data['plate'] in df_f['plate'].values:
        driver_logs = df_f[df_f['plate'] == v_data['plate']].sort_values('created_at', ascending=False)
        st.dataframe(driver_logs[['created_at', 'liters', 'price']].rename(columns={
            'created_at': 'Date', 'liters': 'Liters Added', 'price': 'Price (₹)'
        }), use_container_width=True, hide_index=True)
    else: st.info("No logs found for your vehicle yet.")

    # 3. INPUT FIELDS
    st.divider(); st.subheader("1. Update Odometer")
    no = st.number_input("Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Reading"):
        supabase.table("vehicles").update({"odo": int(no)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer Saved!"); st.rerun()

    st.divider(); st.subheader("2. Diesel Refilled")
    ca, cb = st.columns(2)
    with ca: li = st.number_input("Liters Added", min_value=0.0)
    with cb: pr = st.number_input("Price/Liter (₹)", value=96.20)
    if st.button("Log Fuel & Start New Trip"):
        if li > 0:
            supabase.table("fuel_logs").insert({"plate": v_data['plate'], "driver": st.session_state.user, "liters": float(li), "price": float(pr)}).execute()
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(li)}).eq("plate", v_data['plate']).execute()
            st.success("Trip Reset & Logged!"); st.rerun()

if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()
