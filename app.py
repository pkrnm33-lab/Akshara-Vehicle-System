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

# --- 3. HIGH-VISIBILITY STYLING ---
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

# --- 4. DATA LOADER (PROTECTED) ---
def load_data():
    # Force column structures to prevent KeyError crashes
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
            # Use manual service_date if available, otherwise fallback to created_at
            df_m['display_date'] = pd.to_datetime(df_m.get('service_date', df_m['created_at'])).dt.date
            
        return df_v, df_f, df_m
    except: return df_v, df_f, df_m

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
    t1, t2, t3, t4 = st.tabs(["📊 Performance", "🛠️ Maintenance", "➕ Vehicles", "⚙️ Admin Reset"])
    
    with t1:
        if not df_v.empty:
            report = df_v.copy()
            report['Trip KM'] = report['odo'] - report['trip_km']
            report['Mileage'] = report.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Expenditure Calculation
            fuel_tot = 0
            if not df_f.empty:
                df_f['Cost'] = df_f['liters'] * df_f['price']
                fuel_tot = df_f['Cost'].sum()
                f_sums = df_f.groupby('plate')['Cost'].sum().reset_index().rename(columns={'Cost': 'Fuel ₹'})
                report = report.merge(f_sums, on='plate', how='left').fillna(0)
            else: report['Fuel ₹'] = 0

            maint_tot = 0
            if not df_m.empty:
                maint_tot = df_m['cost'].sum()
                m_sums = df_m.groupby('plate')['cost'].sum().reset_index().rename(columns={'cost': 'Maint ₹'})
                report = report.merge(m_sums, on='plate', how='left').fillna(0)
            else: report['Maint ₹'] = 0

            st.markdown(f'<div class="total-card"><h3 style="margin:0; color:#FFD700;">💰 TOTAL FLEET EXPENDITURE</h3><h1 style="margin:0; color:#FFFFFF;">₹ {fuel_tot + maint_tot:,.2f}</h1><p style="margin:0; font-size:14px;">Diesel: ₹{fuel_tot:,.0f} | Maintenance: ₹{maint_tot:,.0f}</p></div>', unsafe_allow_html=True)
            
            st.write("### 🚌 Fleet Status")
            st.dataframe(report[['plate', 'driver', 'odo', 'Trip KM', 'Mileage', 'Fuel ₹', 'Maint ₹']].rename(columns={
                'plate': 'Bus', 'odo': 'Current Odo'
            }), use_container_width=True, hide_index=True)

    with t2:
        st.subheader("🛠️ Record New Maintenance")
        m_bus = st.selectbox("Select Vehicle", df_v['plate'].unique(), key="m_sel")
        m_date = st.date_input("Service Date", value=datetime.today()) # New Date Picker
        m_type = st.text_input("Work Done (e.g. Engine Oil, Brake Shoe)")
        m_cost = st.number_input("Service Cost (₹)", min_value=0.0)
        
        if st.button("Save Maintenance Record"):
            if m_type and m_cost > 0:
                supabase.table("maintenance_logs").insert({
                    "plate": m_bus, 
                    "service_type": m_type, 
                    "cost": m_cost,
                    "service_date": str(m_date) # Storing specific date
                }).execute()
                st.success("Record Saved!"); st.rerun()
        
        st.divider()
        st.write(f"### 📜 Service History: {m_bus}")
        if not df_m.empty:
            bus_maint = df_m[df_m['plate'] == m_bus].sort_values('display_date', ascending=False)
            if not bus_maint.empty:
                st.dataframe(bus_maint[['display_date', 'service_type', 'cost']].rename(columns={
                    'display_date': 'Date', 'service_type': 'Work Done', 'cost': 'Amount (₹)'
                }), use_container_width=True, hide_index=True)
            else: st.info("No records found for this bus.")

    with t3:
        p_n = st.text_input("Plate Number").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Enroll Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0}).execute()
            st.rerun()

    with t4:
        st.subheader("⚙️ Admin Edit & Reset Tools")
        if not df_v.empty:
            target = st.selectbox("Select Bus to Edit", df_v['plate'].unique())
            v_info = df_v[df_v['plate'] == target].iloc[0]
            
            # Odo & Trip Reset
            st.write("#### 1. Odometer & Trip Controls")
            c1, c2 = st.columns(2)
            with c1:
                new_odo_val = st.number_input("Edit Odo Reading", value=int(v_info['odo']))
                if st.button("Update Odo"):
                    supabase.table("vehicles").update({"odo": int(new_odo_val)}).eq("plate", target).execute()
                    st.rerun()
            with c2:
                st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
                if st.button(f"Reset {target} Trip"):
                    supabase.table("vehicles").update({"trip_km": int(v_info['odo']), "fuel_liters": 0}).eq("plate", target).execute()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Diesel Log Management
            st.divider()
            st.write("#### 2. Diesel Record Editor")
            if not df_f.empty and target in df_f['plate'].values:
                f_log = df_f[df_f['plate'] == target].sort_values('created_at', ascending=False)
                f_id = st.selectbox("Select Diesel Log", f_log['id'], format_func=lambda x: f"Log ID {x}: {f_log[f_log['id']==x]['created_at'].iloc[0].strftime('%d %b')}")
                f_sel = f_log[f_log['id'] == f_id].iloc[0]
                fl, fp = st.columns(2)
                nl = fl.number_input("Correct Liters", value=float(f_sel['liters']))
                np = fp.number_input("Correct Price", value=float(f_sel['price']))
                ce, cd = st.columns(2)
                if ce.button("Update Diesel Log"):
                    supabase.table("fuel_logs").update({"liters": nl, "price": np}).eq("id", f_id).execute()
                    st.rerun()
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if cd.button("Delete Diesel Log"):
                    supabase.table("fuel_logs").delete().eq("id", f_id).execute(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Maintenance Log Management
            st.divider()
            st.write("#### 3. Maintenance Record Editor")
            if not df_m.empty and target in df_m['plate'].values:
                m_log = df_m[df_m['plate'] == target].sort_values('display_date', ascending=False)
                m_id = st.selectbox("Select Maint Log", m_log['id'], format_func=lambda x: f"Log ID {x}: {m_log[m_log['id']==x]['display_date'].iloc[0].strftime('%d %b %Y')}")
                m_sel = m_log[m_log['id'] == m_id].iloc[0]
                nt = st.text_input("Correct Work Done", value=m_sel['service_type'])
                nc = st.number_input("Correct Cost (₹)", value=float(m_sel['cost']))
                me, md = st.columns(2)
                if me.button("Update Maint Log"):
                    supabase.table("maintenance_logs").update({"service_type": nt, "cost": nc}).eq("id", m_id).execute()
                    st.rerun()
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if md.button("Delete Maint Log"):
                    supabase.table("maintenance_logs").delete().eq("id", m_id).execute(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df_v[df_v['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    trip_d = v_data['odo'] - v_data['trip_km']
    st.metric("Trip Distance", f"{trip_d} km")
    
    st.divider(); st.subheader("Update Reading")
    no = st.number_input("Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Reading"):
        supabase.table("vehicles").update({"odo": int(no)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer Saved!"); st.rerun()

    st.divider(); st.subheader("Fuel Entry")
    ca, cb = st.columns(2)
    with ca: li = st.number_input("Liters Added", min_value=0.0)
    with cb: pr = st.number_input("Price/Liter (₹)", value=96.20)
    if st.button("Log Diesel Refill"):
        if li > 0:
            supabase.table("fuel_logs").insert({"plate": v_data['plate'], "driver": st.session_state.user, "liters": float(li), "price": float(pr)}).execute()
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(li)}).eq("plate", v_data['plate']).execute()
            st.success("Fuel Logged!"); st.rerun()

if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()
