import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- Setup ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
DATA_FILE = "vehicle_data.csv"
MSG_FILE = "manager_msg.txt"

# --- Data Handling ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["plate", "driver", "odo", "trip_km", "fuel_liters", "last_updated"])
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_manager_msg():
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE, "r") as f:
            return f.read()
    return ""

def set_manager_msg(msg):
    if msg.strip() == "":
        if os.path.exists(MSG_FILE):
            os.remove(MSG_FILE)
    else:
        timestamp = datetime.now().strftime("%I:%M %p, %d %b")
        full_msg = f"{msg} (Updated: {timestamp})"
        with open(MSG_FILE, "w") as f:
            f.write(full_msg)

# --- App Header ---
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-size: 18px; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)

# --- Driver Notification Bar ---
announcement = get_manager_msg()
if announcement:
    st.warning(f"📢 **MANAGER MESSAGE:** {announcement}")

st.divider()

# --- Login Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login Portal")
    user_input = st.text_input("Username").lower().strip()
    pwd_input = st.text_input
