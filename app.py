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

# --- 3. HIGH-VISIBILITY COLORFUL STYLING ---
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

# --- 4. DATA LOADER ---
def load_data():
    EMPTY_V = pd.DataFrame(columns=['plate', 'driver', 'odo', 'trip_km', 'fuel_liters'])
    EMPTY_F = pd.DataFrame(columns=['id', 'created_at', 'plate', 'driver', 'liters', 'price'])
    try:
        v_res = supabase.table("vehicles").select("*").execute()
        v_df = pd.DataFrame(v_res.data) if v_res.data else EMPTY_V
        try:
            f_res = supabase.table("fuel_logs").select("*").execute()
            if f_res.data:
                f_df = pd.DataFrame(f_res.data)
                f_df['created_at'] = pd.to_datetime(f_df['created_at'])
            else: f_df = EMPTY_F
        except: f_df = EMPTY_F
        return v_df, f_df
    except: return EMPTY_V, EMPTY_F

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
    t1, t2, t3 = st.tabs(["📊 Performance", "➕ Add Vehicle", "⚙️ Admin Reset"])
    
    with t1:
        if not df_v.empty:
            report = df_v.copy()
            report['Trip KM'] = report['odo'] - report['trip_km']
            report['Mileage'] = report.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            if not df_f.empty:
                df_f['Cost'] = df_f['liters'] * df_f['price']
                st.markdown(f'<div class="total-card"><h3 style="margin:0; color:#FFD700;">💰 TOTAL DIESEL EXPENDITURE</h3><h1 style="margin:0; color:#FFFFFF;">₹ {df_f["Cost"].sum():,.2f}</h1></div>', unsafe_allow_html=True)
                
                # --- NEW: BUDGET GOAL ---
                budget_goal = st.sidebar.number_input("Monthly Budget Goal per Bus (₹)", value=10000)
                
                st.write("### 📈 Efficiency Comparison")
                st.bar_chart(report[['plate', 'Mileage']].set_index('plate'))
                st.divider()

                st.write("### 📅 Monthly Diesel Breakdown")
                df_f['Month'] = df_f['created_at'].dt.strftime('%B %Y')
                monthly = df_f.groupby(['plate', 'Month'])['Cost'].sum().reset_index()
                
                # Highlight Over-Budget
                def highlight_budget(val):
                    color = '#FF4B4B' if val > budget_goal else '#FFFFFF'
                    return f'color: {color}'
                
                st.dataframe(monthly.rename(columns={'plate': 'Bus', 'Cost': 'Spent (₹)'}).style.applymap(highlight_budget, subset=['Spent (₹)']), use_container_width=True)
                st.download_button("📥 Download Report", data=monthly.to_csv(index=False), file_name="akshara_monthly.csv")
                st.divider()

                cost_hist = df_f.groupby('plate')['Cost'].sum().reset_index()
                report = report.merge(cost_hist, on='plate', how='left').fillna(0)
            else: report['Cost'] = 0
            
            st.write("### 🚌 Current Trip Mileage")
            st.dataframe(report[['plate', 'driver', 'odo', 'Trip KM', 'fuel_liters', 'Cost', 'Mileage']].rename(columns={
                'plate': 'Bus', 'odo': 'Current Odo', 'fuel_liters': 'Trip Liters', 'Cost': 'Total Cost (₹)'
            }), use_container_width=True, hide_index=True)

    with t2:
        st.subheader("Enroll New Vehicle")
        p_n = st.text_input("Plate Number").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0}).execute()
            st.rerun()

    with t3:
        st.subheader("🔧 Admin Control Panel")
        if not df_v.empty:
            target = st.selectbox("Select Bus", df_v['plate'].unique())
            v_info = df_v[df_v['plate'] == target].iloc[0]
            
            ca, cb = st.columns(2)
            with ca:
                st.markdown("#### 1. Trip Reset")
                st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
                if st.button(f"Reset {target} Trip"):
                    supabase.table("vehicles").update({"trip_km": int(v_info['odo']), "fuel_liters": 0}).eq("plate", target).execute()
                    st.success("Trip fixed!"); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with cb:
                st.markdown("#### 2. Odo Fix")
                new_v = st.number_input("Correct Odo", value=int(v_info['odo']))
                if st.button("Save Odo"):
                    supabase.table("vehicles").update({"odo": int(new_v)}).eq("plate", target).execute()
                    st.success("Updated!"); st.rerun()

            st.markdown("---")
            st.write("#### 3. Edit/Delete Specific Fuel Record")
            if not df_f.empty and target in df_f['plate'].values:
                logs = df_f[df_f['plate'] == target].sort_values('created_at', ascending=False)
                log_id = st.selectbox("Select Log", logs['id'], format_func=lambda x: f"Log {x}: {logs[logs['id']==x]['created_at'].iloc[0].strftime('%d %b')}")
                sel = logs[logs['id'] == log_id].iloc[0]
                l_inp = st.number_input("Liters", value=float(sel['liters']))
                p_inp = st.number_input("Price", value=float(sel['price']))
                ce, cd = st.columns(2)
                if ce.button("Update"):
                    supabase.table("fuel_logs").update({"liters": l_inp, "price": p_inp}).eq("id", log_id).execute()
                    st.rerun()
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if cd.button("Delete Record"):
                    supabase.table("fuel_logs").delete().eq("id", log_id).execute()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.write("#### 4. Total Financial Purge")
            conf = st.checkbox("Confirm Total Purge")
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if st.button("PURGE ALL DIESEL DATA"):
                if conf:
                    supabase.table("fuel_logs").delete().neq("id", 0).execute()
                    supabase.table("vehicles").update({"fuel_liters": 0, "trip_km": 0}).neq("plate", "X").execute()
                    st.success("Reset Complete!"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df_v[df_v['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mil = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    st.columns(2)[0].metric("Trip Distance", f"{trip_dist} km")
    st.columns(2)[1].metric("Efficiency", f"{trip_mil} km/l")
    
    st.divider(); st.subheader("1. Update Odometer")
    new_odo = st.number_input("Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Reading"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Saved!"); st.rerun()

    st.divider(); st.subheader("2. Diesel Refilled")
    ca, cb = st.columns(2)
    with ca: liters = st.number_input("Liters Added", min_value=0.0)
    with cb: price = st.number_input("Price (₹)", value=96.20)
    
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Log Fuel & Start New Trip"):
        if liters > 0:
            supabase.table("fuel_logs").insert({"plate": v_data['plate'], "driver": st.session_state.user, "liters": float(liters), "price": float(price)}).execute()
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(liters)}).eq("plate", v_data['plate']).execute()
            st.success("New Trip Logged!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()
