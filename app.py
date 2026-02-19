import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CLOUD CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Database keys are missing or incorrect in Secrets.")
    st.stop()

# --- 2. APP HEADER ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)
st.divider()

# Load data from your new 'vehicles' table
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- 3. ENROLLMENT SECTION ---
with st.expander("➕ Enroll New Driver"):
    p_n = st.text_input("Plate No (e.g., KA37A8646)").upper().strip()
    d_n = st.text_input("Driver Name").upper().strip()
    
    if st.button("Enroll Now"):
        if p_n and d_n:
            try:
                # Saves data permanently to your cloud project
                supabase.table("vehicles").insert({
                    "plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 1.0
                }).execute()
                st.success(f"Successfully enrolled {d_n} to the cloud!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving to cloud: {e}")
        else:
            st.warning("Please enter both Plate No and Driver Name.")

# --- 4. VIEW DATA ---
if not df.empty:
    st.subheader("Current Fleet Status")
    st.dataframe(df, use_container_width=True)
else:
    st.info("✅ Cloud connection active! Enroll your first driver above.")
