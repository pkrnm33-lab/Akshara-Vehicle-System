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
    user_input = st.text_input("Enter Username").upper().strip()
    
    if st.button("Login"):
        if user_input == "MANAGER":
            st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
        elif not df.empty and user_input in df['driver'].str.upper().values:
            st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
        else:
            st.error("User not found.")
    st.stop()

# --- 4. MANAGER INTERFACE ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    tab1, tab2, tab3 = st.tabs(["Fleet Overview", "Manage Drivers", "System Reset"])
    
    with tab1:
        st.subheader("All Vehicle Performance")
        if not df.empty:
            report_df = df.copy()
            # Shows 'Last Trip Mileage' specifically
            st.dataframe(report_df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Assign Drivers")
        p_n = st.text_input("Plate No").upper()
        d_n = st.text_input("Driver Name").upper()
        if st.button("Confirm Assignment"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success(f"Assigned {d_n} to {p_n}!"); st.rerun()

    with tab3:
        st.subheader("🎯 Individual Vehicle Reset")
        if not df.empty:
            reset_option = st.selectbox("Select Vehicle to Reset", df['plate'].unique())
            if st.button(f"Reset All for {reset_option}"):
                supabase.table("vehicles").update({"fuel_liters": 0.0, "trip_km": 0}).eq("plate", reset_option).execute()
                st.success(f"Records for {reset_option} reset!"); st.rerun()

# --- 5. DRIVER INTERFACE ---
else:
    st.title(f"👋 Welcome, {st.session_state.user}")
    v_data = df[df['driver'].str.upper() == st.session_state.user].iloc[0]
    
    st.metric("Vehicle", v_data['plate'])
    
    # --- MILEAGE LOGIC FIX ---
    # Current trip mileage = KM run since last diesel reset / current diesel amount
    if v_data['fuel_liters'] > 0:
        current_mileage = round(v_data['trip_km'] / v_data['fuel_liters'], 2)
        st.metric("Current Trip Mileage (KM/L)", f"{current_mileage} km/l")
    else:
        st.info("Add diesel to start tracking mileage for this trip.")

    with st.form("odo_log", clear_on_submit=True):
        st.write("### Log New Entry")
        new_odo = st.number_input("Current Odometer Reading (KM)", min_value=int(v_data['odo']), step=1)
        diesel_added = st.number_input("New Diesel Added (Liters)", min_value=0.0, step=0.1)
        
        st.info("💡 Tip: When you fill the tank, the app calculates mileage for the KM run since your last fill.")
        
        if st.form_submit_button("Submit Log"):
            km_run = new_odo - v_data['odo']
            
            # If diesel is added, we consider this a 'completed trip' for mileage
            new_total_trip = v_data['trip_km'] + km_run
            new_total_diesel = v_data['fuel_liters'] + diesel_added
            
            supabase.table("vehicles").update({
                "odo": int(new_odo), 
                "trip_km": int(new_total_trip),
                "fuel_liters": float(new_total_diesel)
            }).eq("plate", v_data['plate']).execute()
            
            st.success("Log saved successfully!")
            st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
