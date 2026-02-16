import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. SECURE DATABASE CONNECTION ---
try:
    # Pulling from Streamlit Cloud Secrets
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ CONNECTION ERROR: Check your Streamlit Secrets.")
    st.info("Make sure you added SUPABASE_URL and SUPABASE_KEY correctly.")
    st.stop()

# --- 2. PAGE SETUP ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)
st.divider()

# Load data from the permanent 'vehicles' table
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login Portal")
    user_input = st.text_input("Username").lower().strip()
    pwd_input = st.text_input("Password", type="password") if user_input == "manager" else ""
    
    if st.button("Login"):
        if user_input == "manager" and pwd_input == "admin":
            st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
        elif not df.empty and user_input in df['driver'].str.lower().values:
            st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
        else:
            st.error("Username not found. Please contact Manager to enroll.")

else:
    # --- 4. MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.header("Manager Control Panel")
        if st.sidebar.button("Logout"): st.session_state.logged_in = False; st.rerun()

        with st.expander("➕ Enroll New Vehicle/Driver"):
            p_n = st.text_input("Plate No").upper()
            d_n = st.text_input("Driver Name").lower()
            if st.button("Enroll Now"):
                supabase.table("vehicles").insert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 1.0}).execute()
                st.success(f"{d_n.upper()} Enrolled!"); st.rerun()

        st.subheader("Live Fleet Status")
        if not df.empty:
            df['AVG (km/l)'] = df.apply(lambda r: round(r['trip_km']/r['fuel_liters'], 2) if r['fuel_liters'] > 0 else 0, axis=1)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Database is empty. Enroll your first driver above.")

    # --- 5. DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        v_data = df[df['driver'].str.lower() == st.session_state.user].iloc[0]
        
        col1, col2 = st.columns(2)
        col1.metric("Odometer", f"{v_data['odo']} km")
        col2.metric("Trip KM", f"{v_data['trip_km']} km")

        new_odo = st.number_input("Update Odometer", min_value=float(v_data['odo']), step=1.0)
        if st.button("Save To Cloud"):
            diff = new_odo - v_data['odo']
            supabase.table("vehicles").update({
                "odo": new_odo, 
                "trip_km": v_data['trip_km'] + diff
            }).eq("plate", v_data['plate']).execute()
            st.success("Saved!"); st.rerun()
