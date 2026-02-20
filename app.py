import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Check Streamlit Secrets.")
    st.stop()

# --- 2. THEME & STYLING ---
st.set_page_config(page_title="Akshara Vehicle System", page_icon="🚌")

# Custom CSS for colorful buttons and headers
st.markdown("""
    <style>
    /* Main School Header */
    .school-header {
        background-color: #FFD700;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #000080;
        margin-bottom: 20px;
    }
    /* Driver Update Button (Blue) */
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
    }
    /* Reset Button (Green) */
    .reset-btn button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 8px !important;
        width: 100% !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADER ---
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 4. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.markdown('<div class="school-header"><h1 style="color:#000080;text-align:center;">🚌 AKSHARA PUBLIC SCHOOL</h1></div>', unsafe_allow_html=True)
    user_input = st.text_input("👤 Enter Username").upper().strip()
    
    if user_input == "MANAGER":
        password = st.text_input("🔐 Manager Password", type="password")
        if st.button("Login as Manager"):
            if password == "Akshara@2026": 
                st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
            else:
                st.error("❌ Invalid Password")
    else:
        if st.button("Login as Driver"):
            if not df.empty and user_input in df['driver'].str.upper().str.strip().values:
                st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
            else:
                st.error("❌ Driver not found.")
    st.stop()

# --- 5. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    st.markdown('<div class="school-header"><h2 style="color:#000080;text-align:center;">🏆 Manager Dashboard</h2></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📊 Fleet Performance", "➕ Enroll Vehicle", "⚙️ Manage"])
    
    with t1:
        if not df.empty:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Highlight mileage color
            def style_mileage(v):
                return 'color: green; font-weight: bold' if v > 12 else 'color: red'
            
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']].style.applymap(style_mileage, subset=['Mileage']), 
                         use_container_width=True, hide_index=True)
            
            csv = m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Excel Report", data=csv, file_name="Akshara_Fleet_Live.csv", mime="text/csv")

    with t2:
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save to Fleet"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.rerun()

    with t3:
        if not df.empty:
            target = st.selectbox("Select Vehicle", df['plate'].unique())
            if st.checkbox(f"Confirm Delete {target}?"):
                if st.button("Delete Permanently"):
                    supabase.table("vehicles").delete().eq("plate", target).execute()
                    st.rerun()

# --- 6. DRIVER INTERFACE ---
else:
    st.markdown(f'<div class="school-header"><h2 style="color:#000080;text-align:center;">👋 Welcome, {st.session_state.user}</h2></div>', unsafe_allow_html=True)
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # CALCULATE METRICS
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    # Colorful Metric Cards
    c1, c2 = st.columns(2)
    c1.metric("📌 Trip Distance", f"{trip_dist} km")
    c2.metric("⛽ Mileage", f"{trip_mileage} km/l")
    
    st.divider()

    # SECTION 1: Blue Button
    st.subheader("1. Daily Odometer Update")
    new_odo = st.number_input("Current Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Update Odometer"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer updated!"); st.rerun()

    st.divider()

    # SECTION 2: Green Button
    st.subheader("2. Fuel Fill-up (Reset)")
    diesel = st.number_input("Diesel Liters Added", min_value=0.0, value=0.0)
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Log Fuel & Start New Trip"):
        if diesel > 0:
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            st.success("Trip reset! Good luck for the next trip."); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
