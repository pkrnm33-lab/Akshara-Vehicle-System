import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- Setup ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
DATA_FILE = "vehicle_data.csv"
HISTORY_FILE = "vehicle_history.csv"
MSG_FILE = "manager_msg.txt"

# --- Data Handling ---
def load_data(file):
    if not os.path.exists(file):
        if file == DATA_FILE:
            df = pd.DataFrame(columns=["plate", "driver", "odo", "trip_km", "fuel_liters", "last_updated"])
        else:
            df = pd.DataFrame(columns=["timestamp", "plate", "driver", "odo", "trip_km", "fuel_liters"])
        df.to_csv(file, index=False)
        return df
    return pd.read_csv(file)

def save_data(df, file):
    df.to_csv(file, index=False)

def get_manager_msg():
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE, "r") as f:
            return f.read()
    return ""

def set_manager_msg(msg):
    with open(MSG_FILE, "w") as f:
        f.write(msg)

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
            df = load_data(DATA_FILE)
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
        
        with st.expander("📢 Send Message to All Drivers"):
            current_msg = get_manager_msg()
            new_msg = st.text_area("Type your message here:", value=current_msg)
            if st.button("Send Message"):
                set_manager_msg(new_msg)
                st.success("Message updated!")
                st.rerun()

        df = load_data(DATA_FILE)
        
        # Download Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(label="📥 Download Excel Report", data=buffer, file_name="Akshara_Report.xlsx")

        # Management Section
        with st.expander("🗑️ Delete Driver or Reset Records"):
            col_a, col_b = st.columns(2)
            with col_a:
                reset_plate = st.selectbox("Reset Vehicle KM", ["None"] + df['plate'].tolist())
                if reset_plate != "None" and st.button("Confirm Reset"):
                    v_idx = df[df['plate'] == reset_plate].index[0]
                    df.at[v_idx, 'odo'] = 0
                    df.at[v_idx, 'trip_km'] = 0
                    df.at[v_idx, 'fuel_liters'] = 0
                    save_data(df, DATA_FILE)
                    st.rerun()
            with col_b:
                del_driver = st.selectbox("Remove Driver Account", ["None"] + df['driver'].tolist())
                if del_driver != "None" and st.button("Confirm Delete"):
                    df = df[df['driver'] != del_driver]
                    save_data(df, DATA_FILE)
                    st.rerun()

        # Enroll Section
        with st.expander("➕ Enroll New Vehicle/Driver"):
            p = st.text_input("Plate No").upper()
            d = st.text_input("Driver Name").lower()
            if st.button("Enroll Now"):
                if p and d:
                    new_row = {"plate": p, "driver": d, "odo": 0, "trip_km": 0, "fuel_liters": 0, "last_updated": "N/A"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df, DATA_FILE)
                    st.rerun()

        st.subheader("Live Vehicle Status Table")
        # --- RE-ADDED MILEAGE CALCULATION ---
        df['AVG (km/l)'] = df.apply(lambda r: round(float(r['trip_km'])/float(r['fuel_liters']), 2) if float(r['fuel_liters']) > 0 else 0.0, axis=1)
        st.dataframe(df, use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        df = load_data(DATA_FILE)
        v_idx_list = df[df['driver'].str.lower() == st.session_state.user].index
        
        if len(v_idx_list) == 0:
            st.error("Account missing. Contact Manager.")
        else:
            v_idx = v_idx_list[0]
            v_data = df.iloc[v_idx]

            # --- MILEAGE FOR DRIVER ---
            try:
                trip, fuel = float(v_data['trip_km']), float(v_data['fuel_liters'])
                avg = round(trip / fuel, 2) if fuel > 0 else 0.0
            except: avg = 0.0

            col1, col2, col3 = st.columns(3)
            col1.metric("Odometer", f"{v_data['odo']} km")
            col2.metric("Trip KM", f"{v_data['trip_km']} km")
            col3.metric("Mileage", f"{avg} km/l") # Re-added here

            # Entry
            new_odo = st.number_input("Enter New Odometer", min_value=float(v_data['odo']), step=1.0)
            if st.button("Update Odometer"):
                diff = new_odo - float(v_data['odo'])
                df.at[v_idx, 'trip_km'] = float(v_data['trip_km']) + diff
                df.at[v_idx, 'odo'] = new_odo
                df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(df, DATA_FILE)
                st.success("Odometer updated!")
                st.rerun()

            st.divider()
            fuel_qty = st.number_input("Diesel Refilled (Liters)", min_value=0.0)
            if st.button("Log Fuel & Reset Trip"):
                df.at[v_idx, 'fuel_liters'] = fuel_qty
                df.at[v_idx, 'trip_km'] = 0
                df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(df, DATA_FILE)
                st.success("Fuel Logged! Trip KM reset.")
                st.rerun()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
