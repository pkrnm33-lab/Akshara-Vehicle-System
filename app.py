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
        # Pulls live data from your vehicles table
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

# --- 4. MANAGER DASHBOARD (WITH MILEAGE COLUMN) ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    t1, t2, t3 = st.tabs(["Fleet Performance", "Enroll Vehicle", "Edit & Delete"])
    
    with t1:
        if not df.empty:
            st.subheader("Live Trip Mileage Report")
            # MIRROR CALCULATION: Mirrors the driver's specific trip logic
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Particular Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Displaying the final table for the Manager
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Particular Mileage']], use_container_width=True, hide_index=True)
        else:
            st.info("No vehicles enrolled.")

    with t2:
        st.subheader("Enroll New Bus")
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("Successfully Enrolled!"); st.rerun()
            
    with t3:
        st.subheader("⚙️ Manage Records")
        if not df.empty:
            target = st.selectbox("Select Vehicle", df['plate'].unique())
            v_row = df[df['plate'] == target].iloc[0]
            with st.expander(f"Edit {target}"):
                new_d = st.text_input("Driver", value=v_row['driver']).upper()
                new_o = st.number_input("Odo Correction", value=int(v_row['odo']))
                if st.button("Update"):
                    supabase.table("vehicles").update({"driver": new_d, "odo": new_o}).eq("plate", target).execute()
                    st.success("Updated!"); st.rerun()
            st.divider()
            if st.checkbox(f"Permanently Delete {target}?"):
                if st.button("Confirm Delete"):
                    supabase.table("vehicles").delete().eq("plate", target).execute()
                    st.warning("Vehicle Removed."); st.rerun()

# --- 5. DRIVER INTERFACE (PRECISE TRIP LOGIC) ---
else:
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # CALCULATE LIVE DASHBOARD
    trip_km = v_data['odo'] - v_data['trip_km']
    mileage = round(trip_km / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    st.write("Current Trip Distance")
    st.title(f"{trip_km} km")
    st.write("Particular Mileage (This Trip)")
    st.title(f"{mileage} km/l")
    st.divider()

    # Update Odometer
    st.write("### 1. Update Daily Meter")
    new_odo = st.number_input("End of Day Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Run"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer updated!"); st.rerun()

    st.divider()

    # Fuel Fill/Reset
    st.write("### 2. Diesel Refilled (Starts New Trip)")
    diesel = st.number_input("Liters Added", min_value=0.0, value=0.0)
    if st.button("Log Fuel & Reset"):
        if diesel > 0:
            # Marker for the next trip
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            st.success("Trip reset! Calculation will start fresh from this meter reading."); st.rerun()
        else:
            st.error("Enter liters added.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
