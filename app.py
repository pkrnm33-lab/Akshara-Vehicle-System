import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CLOUD CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Database connection failed.")
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
        elif not df.empty and user_input in df['driver'].str.upper().values:
            st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
        else:
            st.error("User not found.")
    st.stop()

# --- 4. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    tab1, tab2 = st.tabs(["Fleet Performance", "Admin Tools"])

    with tab1:
        if not df.empty:
            st.subheader("Last Known Mileage per Vehicle")
            # Displaying the last saved mileage calculation
            st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Manage Fleet")
        p_n = st.text_input("New Plate No").upper()
        d_n = st.text_input("New Driver Name").upper()
        if st.button("Add Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.rerun()

# --- 5. DRIVER PORTAL (THE FIX) ---
else:
    st.title(f"👋 Driver: {st.session_state.user}")
    v_data = df[df['driver'].str.upper() == st.session_state.user].iloc[0]
    
    st.info(f"Bus: {v_data['plate']} | Last Odo: {v_data['odo']} KM")

    with st.form("mileage_form"):
        st.write("### Trip Entry")
        new_odo = st.number_input("Current Odometer Reading", min_value=int(v_data['odo']))
        diesel_liters = st.number_input("Diesel Added (Liters)", min_value=0.0)
        
        submit = st.form_submit_button("Calculate Mileage & Save")
        
        if submit:
            km_driven = new_odo - v_data['odo']
            
            if diesel_liters > 0:
                # Calculate mileage for THIS trip specifically
                trip_mileage = round(km_driven / diesel_liters, 2)
                st.success(f"📊 Your Mileage for this trip: {trip_mileage} KM/L")
                
                # UPDATE CLOUD: We update the Odo, and reset the Trip/Diesel for a fresh start
                supabase.table("vehicles").update({
                    "odo": int(new_odo),
                    "trip_km": 0, # Resetting for the next tank fill
                    "fuel_liters": 0.0 # Resetting for the next tank fill
                }).eq("plate", v_data['plate']).execute()
                
            else:
                # If no diesel was added, we just update the total odometer and trip count
                supabase.table("vehicles").update({
                    "odo": int(new_odo),
                    "trip_km": int(v_data['trip_km'] + km_driven)
                }).eq("plate", v_data['plate']).execute()
                st.warning("Odometer updated. Enter diesel next time to see mileage.")
            
            st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
