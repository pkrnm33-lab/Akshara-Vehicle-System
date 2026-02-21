import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. BRANDING & CONFIGURATION ---
LOGO_IMAGE = "1000000180.jpg" 
st.set_page_config(page_title="Akshara Fleet Portal", page_icon="🚌", layout="wide")

# --- 2. DATABASE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Please check your Streamlit Secrets.")
    st.stop()

# --- 3. CUSTOM STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117 !important; }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: #FFFFFF !important; }}
    .branded-header {{ border-bottom: 4px solid #4CAF50; padding: 10px 0 20px 0; margin-bottom: 30px; text-align: center; background-color: #1A1C24; }}
    div[data-testid="stMetricValue"] > div {{ color: #39FF14 !important; font-weight: 800 !important; }}
    div.stButton > button {{ background-color: #2E7D32 !important; color: #FFFFFF !important; border-radius: 8px; font-weight: 700; padding: 12px 20px; width: 100%; }}
    .reset-btn button {{ background-color: #FFD700 !important; color: #000000 !important; }}
    .delete-btn button {{ background-color: #FF4B4B !important; color: #FFFFFF !important; }}
    .total-card {{ background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #FFD700; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. ROBUST DATA LOADER (FIXES ALL CRASHES) ---
def load_data():
    # Force empty dataframes to have correct columns to prevent KeyErrors
    df_v = pd.DataFrame(columns=['plate', 'driver', 'odo', 'trip_km', 'fuel_liters'])
    df_f = pd.DataFrame(columns=['id', 'created_at', 'plate', 'driver', 'liters', 'price'])
    df_m = pd.DataFrame(columns=['id', 'created_at', 'plate', 'service_type', 'cost', 'service_date'])
    
    try:
        v_res = supabase.table("vehicles").select("*").execute()
        if v_res.data: df_v = pd.DataFrame(v_res.data)
        
        f_res = supabase.table("fuel_logs").select("*").execute()
        if f_res.data: 
            df_f = pd.DataFrame(f_res.data)
            df_f['created_at'] = pd.to_datetime(df_f['created_at'])
            
        m_res = supabase.table("maintenance_logs").select("*").execute()
        if m_res.data:
            df_m = pd.DataFrame(m_res.data)
            df_m['service_date'] = pd.to_datetime(df_m.get('service_date', df_m['created_at'])).dt.date
    except: pass
    return df_v, df_f, df_m

df_v, df_f, df_m = load_data()

# --- 5. HEADER COMPONENT ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    try: st.image(LOGO_IMAGE, width=250)
    except: st.markdown('<h1 style="color:#FFFFFF;">AKSHARA PUBLIC SCHOOL</h1>', unsafe_allow_html=True)
    if title: st.markdown(f'<h2 style="color:#4CAF50; font-size:22px;">{title}</h2>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. LOGIN LOGIC ---
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

# --- 7. MANAGER PORTAL ---
if st.session_state.role == "manager":
    draw_header("🏆 MANAGER PORTAL")
    tabs = st.tabs(["📊 Performance", "🛠️ Maintenance", "➕ Add Vehicle", "⚙️ Admin Reset"])
    
    with tabs[0]: # Performance & Monthly Report
        if not df_v.empty:
            report = df_v.copy()
            report['Trip KM'] = report['odo'] - report['trip_km']
            report['Mileage'] = report.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Combine Fuel and Maint Costs
            f_total, m_total = 0, 0
            if not df_f.empty:
                df_f['Cost'] = df_f['liters'] * df_f['price']
                f_total = df_f['Cost'].sum()
                f_sums = df_f.groupby('plate')['Cost'].sum().reset_index().rename(columns={'Cost': 'Fuel ₹'})
                report = report.merge(f_sums, on='plate', how='left').fillna(0)
            else: report['Fuel ₹'] = 0

            if not df_m.empty:
                m_total = df_m['cost'].sum()
                m_sums = df_m.groupby('plate')['cost'].sum().reset_index().rename(columns={'cost': 'Maint ₹'})
                report = report.merge(m_sums, on='plate', how='left').fillna(0)
            else: report['Maint ₹'] = 0

            st.markdown(f'<div class="total-card"><h3 style="margin:0; color:#FFD700;">💰 TOTAL FLEET EXPENDITURE</h3><h1 style="margin:0; color:#FFFFFF;">₹ {f_total + m_total:,.2f}</h1><p style="margin:0; font-size:14px;">Diesel: ₹{f_total:,.0f} | Maint: ₹{m_total:,.0f}</p></div>', unsafe_allow_html=True)
            
            st.write("### 🚌 Fleet Status")
            st.dataframe(report[['plate', 'driver', 'odo', 'Trip KM', 'Mileage', 'Fuel ₹', 'Maint ₹']].rename(columns={'plate': 'Bus', 'odo': 'Current Odo'}), use_container_width=True, hide_index=True)

    with tabs[1]: # Maintenance Tracking
        st.subheader("🛠️ Log New Service")
        m_bus = st.selectbox("Select Vehicle", df_v['plate'].unique(), key="m_bus_mgr")
        m_date = st.date_input("Service Date", value=datetime.today())
        m_type = st.text_input("Work Done (e.g. Oil Change)")
        m_cost = st.number_input("Cost (₹)", min_value=0.0)
        if st.button("Save Record"):
            if m_type and m_cost > 0:
                supabase.table("maintenance_logs").insert({"plate": m_bus, "service_type": m_type, "cost": m_cost, "service_date": str(m_date)}).execute()
                st.success("Maintenance logged!"); st.rerun()
        
        st.divider()
        st.write(f"### 📜 History for {m_bus}")
        if not df_m.empty:
            bus_m = df_m[df_m['plate'] == m_bus].sort_values('service_date', ascending=False)
            st.dataframe(bus_m[['service_date', 'service_type', 'cost']].rename(columns={'service_date': 'Date', 'service_type': 'Work', 'cost': 'Amount'}), use_container_width=True, hide_index=True)

    with tabs[3]: # Admin Tools (ODO, Diesel, Maint Editors)
        st.subheader("⚙️ Admin Control Panel")
        target = st.selectbox("Select Bus to Edit", df_v['plate'].unique())
        v_info = df_v[df_v['plate'] == target].iloc[0]
        
        st.write("#### 1. Fix Odometer & Reset Trip")
        ca, cb = st.columns(2)
        with ca:
            new_odo = st.number_input("Correct Odo", value=int(v_info['odo']))
            if st.button("Update Odometer"):
                supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", target).execute(); st.rerun()
        with cb:
            st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
            if st.button(f"Reset {target} Trip"):
                supabase.table("vehicles").update({"trip_km": int(v_info['odo']), "fuel_liters": 0}).eq("plate", target).
