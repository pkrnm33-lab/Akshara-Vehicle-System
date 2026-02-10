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
    
    # Password field only appears if "manager" is typed
    pwd_input = ""
    if user_input == "manager":
        pwd_input = st.text_input("Manager Password", type="password")
    
    if st.button("Login"):
        if user_input == "manager":
            if pwd_input == "admin":
                st.session_state.role = "manager"
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Incorrect Manager Password")
        elif user_input != "":
            df = load_data()
            if user_input in df['driver'].str.lower().values:
                st.session_state.role = "driver"
                st.session_state.user = user_input
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("User not found. Please contact Manager.")
else:
    # --- MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.sidebar.title("Manager Menu")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.header("Manager Control Panel")
        df = load_data()

        with st.expander("📢 Edit or Delete Driver Message"):
            current_raw_msg = get_manager_msg().split(" (Updated:")[0]
            msg_to_edit = st.text_area("Update message:", value=current_raw_msg)
            if st.button("Update Message"):
                set_manager_msg(msg_to_edit)
                st.rerun()
            if st.button("Clear Message"):
                set_manager_msg("")
                st.rerun()

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(label="📥 Download Excel Report", data=buffer, file_name="Akshara_Report.xlsx")

        with st.expander("🗑️ Delete Driver or Reset Records"):
            col_a, col_b = st.columns(2)
            with col_a:
                reset_p = st.selectbox("Vehicle to Reset", ["None"] + df['plate'].tolist())
                if reset_p != "None" and st.button("Confirm Reset"):
                    v_idx = df[df['plate'] == reset_p].index[0]
                    df.at[v_idx, 'odo'] = 0
                    df.at[v_idx, 'trip_km'] = 0
                    df.at[v_idx, 'fuel_liters'] = 0
                    save_data(df)
                    st.rerun()
            with col_b:
                del_d = st.selectbox("Driver to Remove", ["None"] + df['driver'].tolist())
                if del_d != "None" and st.button("Confirm Delete"):
                    df = df[df['driver'] != del_d]
                    save_data(df)
                    st.rerun()

        with st.expander("➕ Enroll New Vehicle/Driver"):
            p_new = st.text_input("Plate No").upper()
            d_new = st.text_input("Driver Name").lower()
            if st.button("Enroll Now"):
                if p_new and d_new:
                    new_row = {"plate": p_new, "driver": d_new, "odo": 0, "trip_km": 0, "fuel_liters": 0, "last_updated": "N/A"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.rerun()

        st.subheader("Live Vehicle Status Table")
        df['AVG (km/l)'] = df.apply(lambda r: round(float(r['trip_km'])/float(r['fuel_liters']), 2) if float(r['fuel_liters']) > 0 else 0.0, axis=1)
        st.dataframe(df, use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        df = load_data()
        v_idx_list = df[df['driver'].str.lower() == st.session_state.user].index
        if len(v_idx_list) == 0:
            st.error("Account missing. Contact Manager.")
        else:
            v_idx = v_idx_list[0]
            v_data = df.iloc[v_idx]
            try:
                avg = round(float(v_data['trip_km']) / float(v_data['fuel_liters']), 2) if float(v_data['fuel_liters']) > 0 else 0.0
            except: avg = 0.0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Odometer", f"{v_data['odo']} km")
            col2.metric("Trip KM", f"{v_data['trip_km']} km")
            col3.metric("Mileage", f"{avg} km/l")

            new_odo = st.number_input("Enter New Odometer", min_value=float(v_data['odo']), step=1.0)
            if st.button("Update Odometer"):
                df.at[v_idx, 'trip_km'] = float(v_data['trip_km']) + (new_odo - float(v_data['odo']))
                df.at[v_idx, 'odo'] = new_odo
                df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(df)
                st.rerun()
            st.divider()
            fuel_qty = st.number_input("Diesel Refilled (Liters)", min_value=0.0)
            if st.button("Log Fuel & Reset Trip"):
                df.at[v_idx, 'fuel_liters'] = fuel_qty
                df.at[v_idx, 'trip_km'] = 0
                df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(df)
                st.rerun()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
