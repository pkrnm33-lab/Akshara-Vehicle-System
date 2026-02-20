import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CLOUD CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Check Streamlit Secrets.")
    st.stop()

# --- 2. DATA LOADER ---
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
    user_input = st.text_input("Username").upper().strip()
    if st.button("Login"):
        if user_input == "MANAGER":
            st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
        elif not df.empty and user_input in df['driver'].str.upper().str.strip().values:
            st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
        else:
            st.error("User not found.")
    st.stop()

# --- 4. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)

# --- 5. DRIVER INTERFACE (YOUR SPECIFIC LOGIC) ---
else:
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # --- CALCULATION ENGINE ---
    # Trip KM = (Current Odometer) - (Odometer recorded at the LAST fuel fill)
    actual_trip_km = v_data['odo'] - v_data['trip_km']
    
    # Mileage = (Actual Trip KM) / (Diesel liters added at the START of this trip)
    actual_mileage = round(actual_trip_km / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    # LARGE DASHBOARD
    st.write("Current Trip Distance")
    st.title(f"{actual_trip_km} km")
    
    st.write("Particular Mileage (This Trip)")
    st.title(f"{actual_mileage} km/l")
    
    st.divider()

    # STEP 1: DAILY ODOMETER UPDATE
    st.write("### 1. Update Current Meter Reading")
    new_odo = st.number_input("End of Day Odometer", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Daily Run"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success(f"Odometer updated to {new_odo}!"); st.rerun()

    st.divider()

    # STEP 2: FUEL FILL & TRIP RESET
    st.write("### 2. Log New Fuel (Start New Trip)")
    diesel = st.number_input("Liters Added Now", min_value=0.0, value=0.0)
    
    if st.button("Log Fuel & Reset Calculation"):
        if diesel > 0:
            # We save the CURRENT odometer as the 'marker' for the next trip
            # We save the CURRENT liters to divide by in the next trip
            supabase.table("vehicles").update({
                "trip_km": int(v_data['odo']), 
                "fuel_liters": float(diesel)
            }).eq("plate", v_data['plate']).execute()
            
            st.success("New trip started! Your mileage calculation has reset.")
            st.balloons(); st.rerun()
        else:
            st.error("Please enter diesel liters.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
