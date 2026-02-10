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

        # Excel Download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        st.download_button(label="📥 Download Excel Report", data=buffer, file_name="Akshara_Report.xlsx", mime="application/vnd.ms-excel")

        # Edit/Delete Section
        with st.expander("📝 Edit/Delete Driver Records"):
            selected_plate = st.selectbox("Select Vehicle", ["None"] + df['plate'].tolist())
            if selected_plate != "None":
                v_idx = df[df['plate'] == selected_plate].index[0]
                new_driver = st.text_input("Update Driver Name", value=df.at[v_idx, 'driver'])
                if st.button("Save Changes"):
                    df.at[v_idx, 'driver'] = new_driver.lower()
                    save_data(df)
                    st.success("Details Updated!")
                    st.rerun()
                if st.button("🗑️ Delete Vehicle", type="secondary"):
                    df = df[df['plate'] != selected_plate]
                    save_data(df)
                    st.success("Vehicle Removed!")
                    st.rerun()

        # Add New Vehicle
        with st.expander("➕ Enroll New Vehicle"):
            p = st.text_input("Plate No").upper()
            d = st.text_input("Driver Name").lower()
            if st.button("Enroll"):
                if p and d:
                    new_row = {"plate": p, "driver": d, "odo": 0, "trip_km": 0, "fuel_liters": 0, "last_updated": "N/A"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success("Vehicle Enrolled!")
                    st.rerun()

        st.subheader("Live Status & Mileage Alerts")
        
        # Mileage Calculation for Manager Table
        df['AVG (km/l)'] = df.apply(lambda row: round(float(row['trip_km'])/float(row['fuel_liters']), 2) if float(row['fuel_liters']) > 0 else 0.0, axis=1)
        
        # Color Alert Styling
        def color_avg(val):
            color = 'red' if val < 5 and val > 0 else 'white'
            return f'color: {color}'
        
        st.dataframe(df.style.applymap(color_avg, subset=['AVG (km/l)']), use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        df = load_data()
        v_idx = df[df['driver'].str.lower() == st.session_state.user].index[0]
        v_data = df.iloc[v_idx]

        st.info(f"**Vehicle:** {v_data['plate']} | **Current Odo:** {v_data['odo']} km")
        
        # --- LIVE MILEAGE DISPLAY ---
        try:
            trip, fuel = float(v_data['trip_km']), float(v_data['fuel_liters'])
            avg = round(trip / fuel, 2) if fuel > 0 else 0.0
        except: avg = 0.0
        
        # Mileage Notification
        if avg > 0:
            if avg < 5:
                st.warning(f"⚠️ Current Mileage: {avg} km/l (Efficiency is Low)")
            else:
                st.success(f"✅ Current Mileage: {avg} km/l (Good Efficiency)")
        else:
            st.write("--- Start Driving to Calculate Average ---")

        # Update odometer
        new_odo = st.number_input("Enter New Odometer Reading", min_value=float(v_data['odo']), step=1.0)
        if st.button("Update Odometer"):
            diff = new_odo - float(v_data['odo'])
            df.at[v_idx, 'trip_km'] = float(v_data['trip_km']) + diff
            df.at[v_idx, 'odo'] = new_odo
            df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(df
