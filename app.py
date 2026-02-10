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
    pwd_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user_input == "manager" and pwd_input == "admin":
            st.session_state.role = "manager"
            st.session_state.logged_in = True
            st.rerun()
        elif user_input != "":
            df = load_data()
            if user_input in df['driver'].str.lower().values:
                st.session_state.role = "driver"
                st.session_state.user = user_input
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("User not found.")
else:
    # --- MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.sidebar.title("Manager Menu")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.header("Manager Control Panel")
        df = load_data()

        # 1. Edit/Delete Message
        with st.expander("📢 Edit or Delete Driver Message"):
            current_raw_msg = get_manager_msg().split(" (Updated:")[0]
            msg_to_edit = st.text_area("Update your message below:", value=current_raw_msg)
            col1, col2 = st.columns(2)
            if col1.button("✅ Update/Save Message"):
                set_manager_msg(msg_to_edit)
                st.success("Message updated!")
                st.rerun()
            if col2.button("🗑️ Delete Message"):
                set_manager_msg("")
                st.success("Message removed!")
                st.rerun()

        # 2. Excel Report
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(label="
