import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. SECURE DATABASE CONNECTION ---
# This pulls your real keys from the Streamlit Secrets box
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ DATABASE CONNECTION FAILED")
    st.info("Ensure you have replaced the placeholders in Streamlit Secrets with your real Project ID: klvniiwgwyqkvzfbtqa")
    st.stop()

# --- 2. PAGE HEADER ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)
st.divider()

# Load fresh data from your cloud table
def load_data():
    try:
        # Tries to read from your Klvnii... database
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        # Returns empty if the table is still new or empty
        return pd.DataFrame()

df = load_data()

# --- 3. MANAGER ENROLLMENT ---
with st.expander("➕ Enroll New Driver"):
    p_n = st.text_input("Plate No (e.g., KA37A8646)").upper().strip()
    d_n = st.text_input("Driver Name").upper().strip()
    
    if st.button("Enroll Now"):
        if p_n and d_n:
            try:
                # Saves data permanently to klvniiwgwyqkvzfbtqa.supabase.co
                supabase.table("vehicles").insert({
                    "plate": p_n, 
                    "driver": d_n, 
                    "odo": 0, 
                    "trip_km": 0, 
                    "fuel_liters": 1.0
                }).execute()
                st.success(f"Successfully enrolled {d_n}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving to cloud: {e}")
        else:
            st.warning("Please enter both Plate No and Driver Name.")

# --- 4. VIEW LIVE DATA ---
if not df.empty:
    st.subheader("Current Fleet Status")
    # Clean up column names for display
    display_df = df.copy()
    display_df.columns = [c.upper() for c in display_df.columns]
    st.dataframe(display_df, use_container_width=True)
    
    # Simple Logout button for the session
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
else:
    st.info("✅ Database connection active! Enroll your first driver above to see the table.")

# --- 5. DRIVER UPDATE SECTION ---
if not df.empty:
    st.divider()
    st.subheader("Driver Mileage Update")
    selected_driver = st.selectbox("Select Your Name", df['driver'].unique())
    
    if selected_driver:
        v_data = df[df['driver'] == selected_driver].iloc[0]
        current_odo = v_data['odo']
        
        col1, col2 = st.columns(2)
        col1.metric("Last Odometer", f"{current_odo} km")
        col2.metric("Trip KM Run", f"{v_data['trip_km']} km")
        
        new_odo = st.number_input("Enter New Odometer Reading", min_value=float(current_odo), step=1.0)
        
        if st.button("Save Reading to Cloud"):
            diff = new_odo - current_odo
            try:
                supabase.table("vehicles").update({
                    "odo": int(new_odo), 
                    "trip_km": int(v_data['trip_km'] + diff)
                }).eq("plate", v_data['plate']).execute()
                st.success(f"Reading for {v_data['plate']} saved permanently!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update: {e}")
