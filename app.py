import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- Setup ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
DATA_FILE = "vehicle_data.csv"

# --- Data Handling ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["plate", "driver", "odo", "trip_km", "fuel_liters", "last_updated"])
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- App Header ---
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-size: 18px; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)
st.divider()

# --- Login Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login Portal")
    user = st.text_input("Username").lower().strip()
    pwd = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user == "manager" and pwd == "admin":
            st.session_state.role = "manager"
            st.session_state.logged_in = True
            st.rerun()
        else:
            df = load_data()
            if user in df['driver'].str.lower().values:
                st.session_state.role = "driver"
                st.session_state.user = user
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Username or Password")
else:
    # --- MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.sidebar.title("Manager Menu")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.header("Manager Control Panel")
        df = load_data()
        
        # Download Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(label="📥 Download Excel Report", data=buffer, file_name="Akshara_Report.xlsx", mime="application/vnd.ms-excel")

        # Edit Section
        with st.expander("📝 Edit Existing Driver/Vehicle"):
            selected_plate = st.selectbox("Select Vehicle to Edit", df['plate'].tolist())
            if selected_plate:
                v_idx = df[df['plate'] == selected_plate].index[0]
                new_driver = st.text_input("Update Driver", value=df.at[v_idx, 'driver'])
                if st.button("Save Changes"):
                    df.at[v_idx, 'driver'] = new_driver.lower()
                    save_data(df)
                    st.success("Updated!")
                    st.rerun()

        # Delete Section
        with st.expander("🗑️ Delete a Vehicle"):
            delete_plate = st.selectbox("Select Vehicle to Remove", ["None"] + df['plate'].tolist())
            if delete_plate != "None":
                st.warning(f"Are you sure you want to permanently delete {delete_plate}?")
                if st.button("Confirm Delete"):
                    df = df[df['plate'] != delete_plate]
                    save_data(df)
                    st.success(f"Vehicle {delete_plate} removed.")
                    st.rerun()

        # Add Section
        with st.expander("➕ Assign New Vehicle"):
            p = st.text_input("Plate No").upper()
            d = st.text_input("Driver Name").lower()
            if st.button("Enroll Vehicle"):
                if p and d:
                    new_row = {"plate": p, "driver": d, "odo": 0, "trip_km": 0, "fuel_liters": 0, "last_updated": "N/A"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success("Vehicle Enrolled!")
                    st.rerun()

        st.subheader("Live Status Table")
        st.dataframe(df, use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        df = load_data()
        v_idx = df[df['driver'].str.lower() == st.session_state.user].index[0]
        v_data = df.iloc[v_idx]

        st.info(f"**Vehicle:** {v_data['plate']} | **Current Odo:** {v_data['odo']} km")
        
        # Update odometer
        new_odo = st.number_input("Enter New Odometer", min_value=float(v_data['odo']), step=1.0)

        if st.button("Update Odometer"):
            diff = new_odo - float(v_data['odo'])
            df.at[v_idx, 'trip_km'] = float(v_data['trip_km']) + diff
            df.at[v_idx, 'odo'] = new_odo
            df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(df)
            st.success("Data Updated!")
            st.rerun()

        st.divider()
        fuel_qty = st.number_input("Diesel Refilled (L)", min_value=0.0)
        if st.button("Log Fuel & Reset Trip"):
            df.at[v_idx, 'fuel_liters'] = fuel_qty
            df.at[v_idx, 'trip_km'] = 0
            df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(df)
            st.success("Fuel Logged!")
            st.rerun()

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
