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
    t1, t2 = st.tabs(["Fleet Status", "Manage Vehicles"])
    with t1:
        st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)
    with t2:
        st.write("Add or Delete Vehicles here.")

# --- 5. DRIVER INTERFACE (YOUR SPECIFIC LOGIC) ---
else:
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # TRIP CALCULATION
    # 'trip_km' stores the Odometer reading from the LAST time fuel was added
    current_trip_km = v_data['odo'] - v_data['trip_km']
    current_mileage = round(current_trip_km / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    # Dashboard Display
    col1, col2 = st.columns(2)
    col1.metric("Trip KM", f"{current_trip_km} km")
    col2.metric("Mileage", f"{current_mileage} km/l")
    
    st.divider()

    # STEP 1: DAILY ODOMETER UPDATE
    st.write("### Update Current Odometer")
    new_odo = st.number_input("Enter Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Update Odometer"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer updated!"); st.rerun()

    st.divider()

    # STEP 2: FUEL FILL & TRIP RESET
    st.write("### Diesel Refilled (Liters)")
    diesel = st.number_input("Liters Added", min_value=0.0, value=0.0)
    
    if st.button("Log Fuel & Start New Trip"):
        if diesel > 0:
            # We save the CURRENT odometer as the 'trip start point' for next time
            # We save the CURRENT liters to use for the NEXT calculation
            supabase.table("vehicles").update({
                "trip_km": int(v_data['odo']), 
                "fuel_liters": float(diesel)
            }).eq("plate", v_data['plate']).execute()
            
            st.success(f"Trip Reset! Next mileage will be calculated starting from {v_data['odo']} KM.")
            st.balloons(); st.rerun()
        else:
            st.error("Please enter diesel liters.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
