import streamlit as st
from supabase import create_client
import pandas as pd

# --- INITIALIZE SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Akshara Fleet Tracker", layout="wide")

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #4B5563;'>R.G ROAD GANGAVATHI</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- FETCH DATA ---
try:
    response = supabase.table("vehicles").select("*").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Connection Error: {e}")
    df = pd.DataFrame()

# --- SIDEBAR NAVIGATION ---
page = st.sidebar.radio("Select Role", ["📝 Driver Log", "🔐 Manager Login"])

# ==========================================================
# PAGE 1: DRIVER LOG (WITH MILEAGE CALCULATION)
# ==========================================================
if page == "📝 Driver Log":
    st.header("Daily Trip & Fuel Log")
    if not df.empty:
        driver_options = [f"{row['driver']} ({row['plate']})" for _, row in df.iterrows()]
        with st.form("driver_entry", clear_on_submit=True):
            selected_driver = st.selectbox("Identify Yourself", driver_options)
            odo_reading = st.number_input("Current Odometer Reading (KM)", min_value=0)
            fuel_liters = st.number_input("Diesel Added Today (Liters)", min_value=0.0)
            
            if st.form_submit_button("Submit & Calculate Mileage"):
                driver_name = selected_driver.split(" (")[0]
                driver_data = df[df['driver'] == driver_name].iloc[0]
                row_id = driver_data['id']
                
                try:
                    # Update the database
                    supabase.table("vehicles").update({
                        "odo": odo_reading, 
                        "fuel_liters": fuel_liters
                    }).eq("id", row_id).execute()
                    
                    st.success("✅ Log submitted!")

                    # --- MILEAGE DISPLAY ---
                    if fuel_liters > 0:
                        # Calculation: Current KM / Fuel added
                        # Note: For more accuracy, you'd track 'trip_km' between refills
                        mileage = odo_reading / fuel_liters if fuel_liters != 0 else 0
                        
                        st.metric(label="Your Current Trip Mileage", value=f"{mileage:.2f} KM/L")
                        
                        if mileage < 3: # Example threshold for school buses
                            st.warning("⚠️ High fuel consumption detected. Please check for leaks or driving style.")
                        else:
                            st.info("🟢 Good fuel efficiency for this trip.")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("No drivers enrolled.")

# (Manager Login code remains the same as previous version...)
