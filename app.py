import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# --- INITIALIZE SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Akshara Fleet Tracker", layout="wide")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Your Role", ["📝 Driver Log", "🛠️ Manager Dashboard"])

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

# ==========================================================
# PAGE 1: DRIVER LOG
# ==========================================================
if page == "📝 Driver Log":
    st.header("Daily Trip & Fuel Log")
    
    if not df.empty:
        driver_options = [f"{row['driver']} ({row['plate']})" for _, row in df.iterrows()]
        
        with st.form("driver_entry", clear_on_submit=True):
            selected_driver = st.selectbox("Identify Yourself", driver_options)
            odo_reading = st.number_input("Current Odometer Reading (KM)", min_value=0)
            fuel_liters = st.number_input("Diesel Added (Liters)", min_value=0.0)
            
            if st.form_submit_button("Submit Daily Log"):
                # Find the row ID based on the driver's name
                driver_name = selected_driver.split(" (")[0]
                row_id = df[df['driver'] == driver_name]['id'].values[0]
                
                try:
                    supabase.table("vehicles").update({
                        "odo": odo_reading, 
                        "fuel_liters": fuel_liters
                    }).eq("id", row_id).execute()
                    st.success("✅ Your log has been submitted successfully!")
                except Exception as e:
                    st.error(f"Error submitting log: {e}")
    else:
        st.info("No drivers are currently enrolled. Please contact the Manager.")

# ==========================================================
# PAGE 2: MANAGER DASHBOARD
# ==========================================================
elif page == "🛠️ Manager Dashboard":
    st.header("Administrative Controls")
    
    tab1, tab2 = st.tabs(["📊 Fleet Status", "➕ Enrollment & Management"])
    
    with tab1:
        st.subheader("Current Statistics")
        if not df.empty:
            st.dataframe(df[["id", "plate", "driver", "odo", "trip_km", "fuel_liters"]], use_container_width=True, hide_index=True)
        else:
            st.info("No data available.")

    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Enroll New Driver")
            with st.form("enroll_form", clear_on_submit=True):
                p_no = st.text_input("Vehicle Plate Number")
                d_name = st.text_input("Driver Full Name")
                if st.form_submit_button("Confirm Enrollment"):
                    if p_no and d_name:
                        try:
                            supabase.table("vehicles").insert({
                                "plate": p_no, "driver": d_name, "odo": 0, "trip_km": 0, "fuel_liters": 0
                            }).execute()
                            st.success(f"Driver {d_name} is now active!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with col2:
            st.subheader("System Actions")
            if not df.empty:
                driver_to_del = st.selectbox("Select Driver to Remove", df['driver'].tolist())
                if st.button("🗑️ Remove Driver Permanently"):
                    try:
                        supabase.table("vehicles").delete().eq("driver", driver_to_del).execute()
                        st.success(f"Removed {driver_to_del} from the system.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
