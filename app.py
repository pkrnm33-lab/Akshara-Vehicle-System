import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Akshara Fleet Management", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #4B5563;'>R.G ROAD GANGAVATHI</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- FETCH DATA ---
try:
    # Fetch all data from the 'vehicles' table
    response = supabase.table("vehicles").select("*").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    df = pd.DataFrame()

# --- TOP SECTION: ENROLLMENT ---
with st.expander("➕ Enroll New Driver"):
    with st.form("driver_form", clear_on_submit=True):
        p_no = st.text_input("Plate No (e.g., KA37A8646)")
        d_name = st.text_input("Driver Name")
        if st.form_submit_button("Enroll Now"):
            if p_no and d_name:
                try:
                    # Enroll driver with initial 0 values
                    supabase.table("vehicles").insert({
                        "plate": p_no, "driver": d_name, "odo": 0, "trip_km": 0, "fuel_liters": 0
                    }).execute()
                    st.success(f"Driver {d_name} enrolled successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Enrollment Error: {e}")

# --- MIDDLE SECTION: TRIP LOGGING ---
if not df.empty:
    st.subheader("📝 Log Daily Trip & Fuel")
    # Create a list of drivers for the dropdown
    driver_options = [f"{row['driver']} ({row['plate']})" for _, row in df.iterrows()]
    
    with st.form("trip_log", clear_on_submit=True):
        selected_driver = st.selectbox("Select Driver", driver_options)
        new_odo = st.number_input("Current Odometer Reading (KM)", min_value=0)
        fuel_qty = st.number_input("Diesel Added (Liters)", min_value=0.0)
        
        if st.form_submit_button("Update Log"):
            # Find the ID of the selected driver to update their specific row
            driver_name = selected_driver.split(" (")[0]
            row_id = df[df['driver'] == driver_name]['id'].values[0]
            
            try:
                supabase.table("vehicles").update({
                    "odo": new_odo, 
                    "fuel_liters": fuel_qty
                }).eq("id", row_id).execute()
                st.success("Log updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

# --- BOTTOM SECTION: FLEET STATUS ---
st.markdown("---")
st.subheader("📊 Current Fleet Status")
if not df.empty:
    # Display the table clearly
    st.dataframe(df[["id", "plate", "driver", "odo", "trip_km", "fuel_liters"]], use_container_width=True, hide_index=True)
else:
    st.info("No drivers enrolled yet.")
