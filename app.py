import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- Setup ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")

# --- Google Sheets Connection ---
# Replace 'YOUR_SHEET_ID' with the ID from your Google Sheet URL
SHEET_ID = "YOUR_SHEET_ID" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

def load_data_permanent():
    try:
        # Pulls the most fresh data from your Google Sheet
        return pd.read_csv(SHEET_URL)
    except:
        st.error("Cannot connect to Google Sheets. Check your Sheet ID and permissions.")
        return pd.DataFrame(columns=["plate", "driver", "odo", "trip_km", "fuel_liters", "last_updated"])

# Note: Writing back to Sheets requires 'streamlit-gsheets' or a service account.
# For now, we use the load logic. I recommend using the 'Backup' button daily 
# until we set up the Service Account keys for automated writing.

# --- App Header ---
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-size: 18px; color: gray;'>R.G ROAD, GANGAVATHI</h3>", unsafe_allow_html=True)
st.divider()

# --- Login Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login Portal")
    user_input = st.text_input("Username").lower().strip()
    pwd_input = ""
    if user_input == "manager":
        pwd_input = st.text_input("Manager Password", type="password")
    
    if st.button("Login"):
        if user_input == "manager" and pwd_input == "admin":
            st.session_state.role = "manager"
            st.session_state.logged_in = True
            st.rerun()
        elif user_input != "":
            df = load_data_permanent()
            if user_input in df['driver'].str.lower().values:
                st.session_state.role = "driver"
                st.session_state.user = user_input
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("User not found in the permanent database.")

else:
    # --- MANAGER VIEW ---
    if st.session_state.role == "manager":
        st.header("Manager Control Panel")
        df = load_data_permanent()
        
        # PERMANENT BACKUP BUTTON
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="💾 Download Permanent Backup (Excel)", 
            data=buffer, 
            file_name=f"Akshara_Backup_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            help="Download this daily to ensure you never lose data even if the app sleeps."
        )

        st.subheader("Live Fleet Status")
        st.dataframe(df, use_container_width=True)

    # --- DRIVER VIEW ---
    else:
        st.header(f"Driver Portal: {st.session_state.user.upper()}")
        df = load_data_permanent()
        # Filter for the specific driver
        v_data = df[df['driver'].str.lower() == st.session_state.user].iloc[0]
        
        st.metric("Current Odometer", f"{v_data['odo']} km")
        # Update Logic here...
