import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. BRANDING & CONFIG ---
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

# --- 3. STYLING (DARK THEME & NEON METRICS) ---
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

# --- 4. DATA LOADER (FIXED FOR NameError & KeyError) ---
def load_data():
    # Initialize empty dataframes with correct columns
    df_v = pd.DataFrame(columns=['plate', 'driver', 'odo', 'trip_km', 'fuel_liters'])
    df_f = pd.DataFrame(columns=['id', 'created_at', 'plate', 'driver', 'liters', 'price'])
    df_m = pd.DataFrame(columns=['id', 'created_at', 'plate', 'service_type', 'cost'])
    
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
            df_m['created_at'] = pd.to_datetime(df_m['created_at'])
    except Exception as e:
        st.warning(f"Database sync issue: {e}")
        
    return df_v, df_f, df_m

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
    t1, t2, t3, t4 = st.tabs(["📊 Performance", "🛠️ Log Maintenance", "➕ Vehicles", "⚙️ Admin"])
    
    with t1:
        if not df_v.empty:
            report = df_v.copy()
            report['Trip KM'] = report['odo'] - report['trip_km']
            report['Mileage'] = report.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Sum Costs
            fuel_total = 0
            if not df_f.empty:
                df_f['Cost'] = df_f['liters'] * df_f['price']
                fuel_total = df_f['Cost'].sum()
                f_sums = df_f.groupby('plate')['Cost'].sum().reset_index().rename(columns={'Cost': 'Fuel Cost'})
                report = report.merge(f_sums, on='plate', how='left').fillna(0)
            else: report['Fuel Cost'] = 0

            maint_total = 0
            if not df_m.empty:
                maint_total = df_m['cost'].sum()
                m_sums = df_m.groupby('plate')['cost'].sum().reset_index().rename(columns={'cost': 'Maint Cost'})
                report = report.merge(m_sums, on='plate', how='left').fillna(0)
            else: report['Maint Cost'] = 0

            # Combined Expenditure Card
            st.markdown(f"""
                <div class="total-card">
                    <h3 style="margin:0; color:#FFD700;">💰 TOTAL SCHOOL EXPENDITURE</h3>
                    <h1 style="margin:0; color:#FFFFFF;">₹ {fuel_total + maint_total:,.2f}</h1>
                    <p style="margin:0; font-size:14px;">Diesel: ₹{fuel_total:,.0f} | Maint: ₹{maint_total:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("### 🚌 Vehicle Performance & Costs")
            st.dataframe(report[['plate', 'driver', 'odo', 'Trip KM', 'Mileage', 'Fuel Cost', 'Maint Cost']].rename(columns={
                'plate': 'Bus', 'odo': 'Current Odo', 'Fuel Cost': 'Fuel (₹)', 'Maint Cost': 'Maint (₹)'
            }), use_container_width=True, hide_index=True)

    with t2:
        st.subheader("Record New Repair or Service")
        m_bus = st.selectbox("Select Bus", df_v['plate'].unique())
        m_type = st.text_input("Service Type (e.g., Oil Change, New Tyres)")
        m_cost = st.number_input("Cost (₹)", min_value=0.0)
        if st.button("Save Maintenance"):
            if m_type and m_cost > 0:
                supabase.table("maintenance_logs").insert({"plate": m_bus, "service_type": m_type, "cost": m_cost}).execute()
                st.success("Maintenance logged!"); st.rerun()

    with t3:
        p_n = st.text_input("Plate Number").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0}).execute()
            st.rerun()

    with t4:
        st.subheader("Admin Reset Controls")
        if not df_v.empty:
            target = st.selectbox("Manage Bus", df_v['plate'].unique())
            v_info = df_v[df_v['plate'] == target].iloc[0]
            
            if st.button(f"Reset Trip for {target}"):
                supabase.table("vehicles").update({"trip_km": int(v_info['odo']), "fuel_liters": 0}).eq("plate", target).execute()
                st.rerun()
            
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if st.button(f"Delete Vehicle {target}"):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                supabase.table("fuel_logs").delete().eq("plate", target).execute()
                supabase.table("maintenance_logs").delete().eq("plate", target).execute()
                st.success("Vehicle and all data removed."); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df_v[df_v['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    trip_dist = v_data['odo'] - v_data['trip_km']
    st.metric("Trip Distance", f"{trip_dist} km")
    
    st.divider(); st.subheader("Update Odometer")
    new_odo = st.number_input("Current Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Odo"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Saved!"); st.rerun()

    st.divider(); st.subheader("Diesel Refill")
    ca, cb = st.columns(2)
    with ca: liters = st.number_input("Liters", min_value=0.0)
    with cb: price = st.number_input("Price (₹)", value=96.20)
    if st.button("Log Fuel"):
        if liters > 0:
            supabase.table("fuel_logs").insert({"plate": v_data['plate'], "driver": st.session_state.user, "liters": float(liters), "price": float(price)}).execute()
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(liters)}).eq("plate", v_data['plate']).execute()
            st.success("Fuel Saved!"); st.rerun()

if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()
