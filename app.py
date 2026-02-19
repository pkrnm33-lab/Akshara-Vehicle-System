import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. CLOUD CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Database connection failed. Check Streamlit Secrets.")
    st.stop()

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Akshara Vehicle System", layout="centered", page_icon="🚌")

# Load data helper
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
    st.subheader("Login Portal")
    user_input = st.text_input("Enter Username (Manager or Driver Name)").upper().strip()
    
    if st.button("Login"):
        if user_input == "MANAGER":
            st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
        elif not df.empty and user_input in df['driver'].str.upper().values:
            st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
        else:
            st.error("User not found. Check spelling or contact Manager.")
    st.stop()

# --- 4. MANAGER INTERFACE ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["Fleet Overview", "Manage Drivers", "System Reset"])
    
    with tab1:
        st.subheader("All Vehicle Mileage")
        if not df.empty:
            # Calculate mileage (KM per Liter)
            report_df = df.copy()
            report_df['mileage'] = report_df.apply(lambda x: round(x['trip_km'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            st.dataframe(report_df[['plate', 'driver', 'odo', 'trip_km', 'mileage']], use_container_width=True, hide_index=True)
        else:
            st.info("No vehicles registered.")

    with tab2:
        st.subheader("Assign/Update Drivers")
        p_n = st.text_input("Vehicle Plate No (e.g., KA37A8646)").upper()
        d_n = st.text_input("Assign Driver Name").upper()
        if st.button("Confirm Assignment"):
            # Insert or update based on plate
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success(f"Driver {d_n} assigned to {p_n}!"); st.rerun()

    with tab3:
        st.warning("⚠️ Critical Actions")
        if st.button("RESET ALL RECORDS"):
            for _, row in df.iterrows():
                supabase.table("vehicles").update({"trip_km": 0, "fuel_liters": 0.0}).eq("plate", row['plate']).execute()
            st.success("All trip records reset for a new month!"); st.rerun()

# --- 5. DRIVER INTERFACE ---
else:
    st.title(f"👋 Welcome, {st.session_state.user}")
    v_data = df[df['driver'].str.upper() == st.session_state.user].iloc[0]
    
    st.metric("Your Vehicle", v_data['plate'])
    mileage = round(v_data['trip_km'] / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    st.metric("Current Mileage (KM/L)", f"{mileage} km/l")

    with st.form("odo_log", clear_on_submit=True):
        new_odo = st.number_input("Update Odometer (KM)", min_value=int(v_data['odo']), step=1)
        diesel = st.number_input("Diesel Added (Liters)", min_value=0.0, step=0.1)
        if st.form_submit_button("Save Log"):
            diff = new_odo - v_data['odo']
            supabase.table("vehicles").update({
                "odo": int(new_odo), 
                "trip_km": int(v_data['trip_km'] + diff),
                "fuel_liters": float(v_data['fuel_liters'] + diesel)
            }).eq("plate", v_data['plate']).execute()
            st.success("Log saved successfully!"); st.rerun()

# Shared Logout
if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
