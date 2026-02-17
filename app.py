import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Akshara Vehicle System", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

BASE_URL = f"{URL}/rest/v1/vehicles"

st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.divider()

# ---------------- LOAD DATA ----------------
def load_data():
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(response.text)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

df = load_data()

# ---------------- ENROLL ----------------
with st.expander("➕ Enroll New Driver"):
    plate_no = st.text_input("Plate No").upper()
    driver_name = st.text_input("Driver Name").upper()

    if st.button("Enroll Now"):

        if plate_no == "" or driver_name == "":
            st.warning("Please fill all fields.")
        else:
            data = {
                "plate": plate_no,
                "driver": driver_name,
                "odo": 0,
                "trip_km": 0,
                "fuel_liters": 1.0
            }

            try:
                response = requests.post(BASE_URL, headers=HEADERS, json=data)

                if response.status_code in [200, 201]:
                    st.success("Driver enrolled successfully!")
                    st.rerun()
                else:
                    st.error(response.text)

            except Exception as e:
                st.error(f"Insertion Error: {e}")

# ---------------- DISPLAY ----------------
if not df.empty:
    st.subheader("Current Fleet Status")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Database is empty. Enroll your first driver above.")
