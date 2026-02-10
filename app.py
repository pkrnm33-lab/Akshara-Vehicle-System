import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- Setup ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
DATA_FILE = "vehicle_data.csv"

# --- Data Handling Functions ---
def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["plate", "driver", "odo", "trip_km", "fuel_liters", "last_updated", "location"])
        df.to_csv(DATA_FILE, index=False)
        return df
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- App Header ---
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-size: 18px; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)
st.divider()

# --- Authentication Logic ---
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
                st.error("Invalid Credentials")
else:
    # --- MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.sidebar.title("Manager Menu")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.header("Manager Control Panel") # Fixed: closed string and bracket here
        df = load_data()
        
        # Action Bar: Excel Download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(label="📥 Download Excel Report", data=buffer, file_name=f"Akshara_Vehicle_Report.xlsx", mime="application/vnd.ms-excel")

        # --- Edit Existing Driver Section ---
        with st.expander("📝 Edit Existing Driver/Vehicle"):
            selected_plate = st.selectbox("Select Vehicle to Edit", df['plate'].tolist())
            if selected_plate:
                v_idx = df[df['plate'] == selected_plate].index[0]
                new_driver_name = st.text_input("Update Driver Name", value=df.at[v_idx, 'driver'])
                new_plate_no = st.text_input("Update Plate Number", value=df.at[v_idx, 'plate'])
                
                if st.button("Confirm Changes"):
                    df.at[v_idx, 'driver'] = new_driver_name.lower()
                    df.at[v_idx, 'plate'] = new_plate_no.upper()
                    save_data(df)
                    st.success("Details updated successfully!")
                    st.rerun()

        # Add New Vehicle Section
        with st.expander("➕ Assign/Edit New Vehicle"):
            p = st.text_input("Plate No (e.g., KA37...)").upper()
            d = st.text_input("Driver Name").lower()
            if st.button("Save to System"):
                if p and d:
                    new_row = {"plate": p, "driver": d, "odo": 0, "trip_km": 0, "fuel_liters": 0, "last_updated": "N/A", "location": "N/A"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success(f"Vehicle {p} assigned to {d}!")
                    st.rerun()

        st.subheader("Live Vehicle Status")
        st.dataframe(df, use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal:
