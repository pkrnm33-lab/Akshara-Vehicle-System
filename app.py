import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SECURE CONNECTION ---
try:
    # This pulls your real keys from the Secrets box you just updated
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ DATABASE KEYS ARE NOT CONFIGURED")
    st.info("Please replace the placeholders in Streamlit Secrets with your real keys.")
    st.stop()

# --- 2. HEADER ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.divider()

# Load fresh data from the 'vehicles' table
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.warning(f"Waiting for your first driver to be enrolled... (Error: {e})")
        return pd.DataFrame()

df = load_data()

# --- 3. ENROLLMENT SECTION ---
with st.expander("➕ Enroll New Driver"):
    p_n = st.text_input("Plate No (e.g., KA37A8646)").upper()
    d_n = st.text_input("Driver Name").upper()
    if st.button("Enroll Now"):
        try:
            # Saves data permanently to klvniiwgwyqkvzfbtqa.supabase.co
            supabase.table("vehicles").insert({
                "plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 1.0
            }).execute()
            st.success(f"Successfully enrolled {d_n}!"); st.rerun()
        except Exception as e:
            st.error(f"Failed to save to cloud: {e}")

# --- 4. VIEW DATA ---
if not df.empty:
    st.subheader("Current Fleet Status")
    st.dataframe(df, use_container_width=True)
