import streamlit as st
from supabase import create_client, Client

# -------------------------
# SUPABASE CONFIG
# -------------------------

SUPABASE_URL = "https://klvniiwgwiyqkvzfb tqa.supabase.co"
SUPABASE_KEY = "PASTE_YOUR_ANON_PUBLIC_KEY_HERE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# PAGE SETTINGS
# -------------------------

st.set_page_config(page_title="Akshara Public School", layout="centered")

st.title("AKSHARA PUBLIC SCHOOL")

# -------------------------
# LOAD DATA
# -------------------------

try:
    response = supabase.table("vehicles").select("*").execute()
    data = response.data
except Exception as e:
    st.error(f"Data Load Error: {e}")
    data = []

# -------------------------
# ENROLL NEW DRIVER
# -------------------------

with st.expander("➕ Enroll New Driver"):
    plate = st.text_input("Vehicle Plate")
    driver = st.text_input("Driver Name")
    odo = st.number_input("Odometer Reading", min_value=0)
    trip_km = st.number_input("Trip KM", min_value=0)
    fuel_liters = st.number_input("Fuel Liters", min_value=0.0)

    if st.button("Save"):
        try:
            supabase.table("vehicles").insert({
                "plate": plate,
                "driver": driver,
                "odo": odo,
                "trip_km": trip_km,
                "fuel_liters": fuel_liters
            }).execute()

            st.success("Driver enrolled successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Insert Error: {e}")

# -------------------------
# SHOW DATA
# -------------------------

if data:
    st.dataframe(data)
else:
    st.warning("Database is empty. Enroll your first driver above.")
