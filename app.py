import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONNECTION ---
try:
    # Pulls the real keys you just saved in Secrets
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Database keys are not set correctly in Secrets.")
    st.stop()

# --- 2. HEADER ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.divider()

# Load fresh data
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.warning(f"Waiting for your first driver to be enrolled... (Error: {e})")
        return pd.DataFrame()

df = load_data()

# --- 3. ENROLLMENT ---
with st.expander("➕ Enroll New Driver"):
    p_n = st.text_input("Plate No").upper()
    d_n = st.text_input("Driver Name").upper()
    if st.button("Enroll Now"):
        # This saves data permanently to klvniiwgwyqkvzfbtqa.supabase.co
        supabase.table("vehicles").insert({
            "plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 1.0
        }).execute()
        st.success(f"Successfully enrolled {d_n}!"); st.rerun()

# --- 4. VIEW DATA ---
if not df.empty:
    st.subheader("Current Fleet Status")
    st.dataframe(df, use_container_width=True)
