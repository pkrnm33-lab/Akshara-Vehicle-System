import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- Setup ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
DATA_FILE = "vehicle_data.csv"

# --- Data Logic ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["plate", "driver", "odo", "trip_km", "fuel_liters", "last_updated"])
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- Authentication Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("School Vehicle Portal")
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
                st.error("Invalid Credentials")
else:
    # --- MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.sidebar.title("Manager Menu")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.header("Manager Control Panel")
        df = load_data()
        
        # Action Bar
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("All Vehicles")
        with col2:
            # --- NEW EXCEL DOWNLOAD BUTTON ---
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 Download Excel Report",
                data=buffer,
                file_name=f"Akshara_Vehicle_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.ms-excel"
            )

        # Assignment Section
        with st.expander("➕ Assign/Edit New Vehicle"):
            p = st.text_input("Plate No (e.g., KA37...)").upper()
            d = st.text_input("Driver Name").lower()
            if st.button("Save to System"):
                if p and d:
                    new_row = {"plate": p, "driver": d, "odo": 0, "trip_km": 0, "fuel_liters": 0, "last_updated": "N/A"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success(f"Vehicle {p} assigned to {d}!")
                    st.rerun()
                else:
                    st.warning("Please enter both plate and driver.")

        st.dataframe(df, use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        df = load_data()
        v_idx = df[df['driver'].str.lower() == st.session_state.user].index[0]
        v_data = df.iloc[v_idx]

        st.info(f"**Vehicle:** {v_data['plate']} | **Current Odo:** {v_data['odo']} km")
        
        # Calculations for Live Average
        try:
            trip_val = float(v_data['trip_km'])
            fuel_val = float(v_data['fuel_liters'])
            avg = round(trip_val / fuel_val, 2) if fuel_val > 0 else 0.0
        except: avg = 0.0
        
        st.metric("Live Mileage Average", f"{avg} km/l")

        # Odometer Update
        new_odo = st.number_input("Enter Current Odometer", min_value=float(v_data['odo']), step=1.0)
        if st.button("Update Odometer"):
            diff = new_odo - float(v_data['odo'])
            df.at[v_idx, 'trip_km'] = float(v_data['trip_km']) + diff
            df.at[v_idx, 'odo'] = new_odo
            df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(df)
            st.success("Odometer Updated!")
            st.rerun()

        st.divider()
        
        # Fuel Update
        fuel_qty = st.number_input("Diesel Refilled (Liters)", min_value=0.0, step=1.0)
        if st.button("Log Fuel & Reset Trip"):
            df.at[v_idx, 'fuel_liters'] = fuel_qty
            df.at[v_idx, 'trip_km'] = 0
            df.at[v_idx, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(df)
            st.success("Fuel Logged! Trip distance reset for new tank.")
            st.rerun()

        if st.button("Logout", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
