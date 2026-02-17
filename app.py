import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")

# -------------------------------
# CONNECT TO SUPABASE
# -------------------------------
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]

    supabase = create_client(URL, KEY)

except Exception as e:
    st.error("⚠️ Failed to connect to Supabase.")
    st.error(str(e))
    st.stop()

# -------------------------------
# HEADER
# -------------------------------
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.divider()

# -------------------------------
# LOAD DATA FUNCTION
# -------------------------------
def load_data():
    try:
        response = supabase.table("vehicles").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

df = load_data()

# -------------------------------
# ENROLL NEW DRIVER
# -------------------------------
with st.expander("➕ Enroll New Driver"):
    plate_no = st.text_input("Plate No").upper()
    driver_name = st.text_input("Driver Name").upper()

    if st.button("Enroll Now"):

        if plate_no == "" or driver_name == "":
            st.warning("Please fill all fields.")
        else:
            try:
                supabase.table("vehicles").insert({
                    "plate": plate_no,
                    "driver": driver_name,
                    "odo": 0,
                    "trip_km": 0,
                    "fuel_liters": 1.0
                }).execute()

                st.success(f"Successfully enrolled {driver_name}!")
                st.rerun()

            except Exception as e:
                st.error(f"Insertion Error: {e}")

# -------------------------------
# DISPLAY DATA
# -------------------------------
if not df.empty:
    st.subheader("Current Fleet Status")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Database is empty. Enroll your first driver above.")
