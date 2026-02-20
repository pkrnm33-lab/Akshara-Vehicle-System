import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CLOUD CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection failed. Check Streamlit Secrets.")
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
    t1, t2, t3 = st.tabs(["Fleet Status", "Add Vehicle", "Manage & Delete"])
    
    with t1:
        if not df.empty:
            st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)
    
    with t2:
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Add to Fleet"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("Vehicle Added!"); st.rerun()
            
    with t3:
        if not df.empty:
            target = st.selectbox("Select Vehicle", df['plate'].unique())
            confirm = st.checkbox(f"Confirm Delete {target}?")
            if st.button("Delete Vehicle", disabled=not confirm):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.rerun()

# --- 5. DRIVER INTERFACE (MATCHING YOUR IMAGE) ---
else:
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # Dashboard Header
    st.write("Trip KM")
    st.title(f"{v_data['trip_km']} km")
    
    # Calculate Mileage
    mileage = round(v_data['trip_km'] / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    st.write("Mileage")
    st.title(f"{mileage} km/l")
    
    st.divider()

    # Step 1: Update Odometer Only
    st.write("Enter New Odometer")
    new_odo = st.number_input("Odo Reading", min_value=float(v_data['odo']), value=float(v_data['odo']), label_visibility="collapsed")
    if st.button("Update Odometer"):
        km_run = new_odo - v_data['odo']
        supabase.table("vehicles").update({
            "odo": int(new_odo),
            "trip_km": int(v_data['trip_km'] + km_run)
        }).eq("plate", v_data['plate']).execute()
        st.success("Odometer Updated!"); st.rerun()

    st.divider()

    # Step 2: Log Fuel & Finalize Trip
    st.write("Diesel Refilled (Liters)")
    diesel = st.number_input("Diesel Refilled", min_value=0.0, value=0.0, label_visibility="collapsed")
    if st.button("Log Fuel & Reset Trip"):
        if diesel > 0:
            # We calculate mileage based on current trip before resetting
            supabase.table("vehicles").update({
                "fuel_liters": float(diesel)
            }).eq("plate", v_data['plate']).execute()
            st.success(f"Final Trip Mileage: {round(v_data['trip_km']/diesel, 2)} km/l")
            
            # Resetting for next cycle
            supabase.table("vehicles").update({"trip_km": 0, "fuel_liters": 0.0}).eq("plate", v_data['plate']).execute()
            st.rerun()
        else:
            st.warning("Please enter diesel amount to calculate mileage.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
