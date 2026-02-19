import streamlit as st
from supabase import create_client
import pandas as pd

# --- INITIALIZE SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Akshara Fleet Tracker", layout="wide")

# --- CUSTOM CSS FOR LOGIN ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1E3A8A; color: white; }
    .main { background-color: #F8FAFC; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Your Role", ["📝 Driver Log", "🔐 Manager Login"])

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #4B5563;'>R.G ROAD GANGAVATHI</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- FETCH DATA ---
try:
    response = supabase.table("vehicles").select("*").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Connection Error: {e}")
    df = pd.DataFrame()

# ==========================================================
# PAGE 1: DRIVER LOG (Public Access)
# ==========================================================
if page == "📝 Driver Log":
    st.header("Daily Trip & Fuel Log")
    if not df.empty:
        driver_options = [f"{row['driver']} ({row['plate']})" for _, row in df.iterrows()]
        with st.form("driver_entry", clear_on_submit=True):
            selected_driver = st.selectbox("Identify Yourself", driver_options)
            odo_reading = st.number_input("Current Odometer Reading (KM)", min_value=0)
            fuel_liters = st.number_input("Diesel Added (Liters)", min_value=0.0)
            if st.form_submit_button("Submit Daily Log"):
                driver_name = selected_driver.split(" (")[0]
                row_id = df[df['driver'] == driver_name]['id'].values[0]
                try:
                    supabase.table("vehicles").update({"odo": odo_reading, "fuel_liters": fuel_liters}).eq("id", row_id).execute()
                    st.success("✅ Log submitted successfully!")
                except Exception as e:
                    st.error(
