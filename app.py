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
    .branded-header {{ border-bottom: 4px solid #4CAF50; padding: 10px 0 20px 0; margin-bottom: 30px; text-align: center; background-color: #1A1C24; }}
    div[data-testid="stMetric"] {{ background: #1A1C24 !important; border: 1px solid #4CAF50 !important; border-radius: 12px; padding: 15px; }}
    div[data-testid="stMetricValue"] > div {{ color: #39FF14 !important; font-weight: 800 !important; }}
    div.stButton > button {{ background-color: #2E7D32 !important; color: #FFFFFF !important; border-radius: 8px; font-weight: 700; padding: 12px 20px; width: 100%; }}
    .reset-btn button {{ background-color: #FFD700 !important; color: #000000 !important; }}
    .total-card {{ background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #FFD700; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA LOADER ---
def load_data():
    try:
        v_res = supabase.table("vehicles").select("*").execute()
        v_df = pd.DataFrame(v_res.data)
        try:
            f_res = supabase.table("fuel_logs").select("*").execute()
            f_df = pd.DataFrame(f_res.data)
        except: f_df = pd.DataFrame()
        return v_df, f_df
    except: return pd.DataFrame(), pd.DataFrame()

df_v, df_f = load_data()

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
    t1, t2 = st.tabs(["📊 Performance", "➕ Add Vehicle"])
    
    with t1:
        if not df_v.empty:
            report = df_v.copy()
            # CALCULATION: Current Odo - Starting Odo of THIS trip
            report['Trip KM'] = report['odo'] - report['trip_km']
            # CALCULATION: Trip KM / Liters from LAST refill
            report['Mileage'] = report.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Show Total Expenditure Card
            if not df_f.empty:
                df_f['Cost'] = df_f['liters'] * df_f['price']
                st.markdown(f'<div class="total-card"><h3 style="margin:0; color:#FFD700;">💰 TOTAL DIESEL EXPENDITURE</h3><h1 style="margin:0; color:#FFFFFF;">₹ {df_f["Cost"].sum():,.2f}</h1></div>', unsafe_allow_html=True)
            
            st.dataframe(report[['plate', 'driver', 'odo', 'Trip KM', 'fuel_liters', 'Mileage']].rename(columns={
                'plate': 'Bus', 'odo': 'Current Odo', 'fuel_liters': 'Trip Liters'
            }), use_container_width=True, hide_index=True)

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df_v[df_v['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # Calculate Live Trip Stats for Driver
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    c1, c2 = st.columns(2)
    c1.metric("Trip Distance", f"{trip_dist} km")
    c2.metric("Efficiency", f"{trip_mileage} km/l")
    
    st.divider()
    st.subheader("1. Update Odometer")
    new_odo = st.number_input("Current Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Reading"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer Saved!"); st.rerun()

    st.divider()
    st.subheader("2. Diesel Refilled")
    ca, cb = st.columns(2)
    with ca: liters = st.number_input("Liters Added", min_value=0.0)
    with cb: price = st.number_input("Price/Liter (₹)", min_value=0.0, value=96.20)
    
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Log Fuel & Start New Trip"):
        if liters > 0:
            # 1. Save refill to permanent history log
            supabase.table("fuel_logs").insert({"plate": v_data['plate'], "driver": st.session_state.user, "liters": float(liters), "price": float(price)}).execute()
            
            # 2. Reset Trip: Set start Odo to NOW and save these Liters
            supabase.table("vehicles").update({
                "trip_km": int(v_data['odo']), 
                "fuel_liters": float(liters)
            }).eq("plate", v_data['plate']).execute()
            
            st.success("New Trip Started!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()
