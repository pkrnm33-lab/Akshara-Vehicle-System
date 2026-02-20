import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CLOUD CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Database connection failed. Check Streamlit Secrets.")
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

# --- 4. MANAGER DASHBOARD (WITH EDIT/DELETE) ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    tab1, tab2, tab3 = st.tabs(["Fleet Status", "Add Vehicle", "Edit & Delete"])

    with tab1:
        st.subheader("Live Performance")
        if not df.empty:
            st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Enroll New Vehicle")
        p_n = st.text_input("Plate No").upper()
        d_n = st.text_input("Driver Name").upper()
        if st.button("Save to Fleet"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("Saved!"); st.rerun()

    with tab3:
        st.subheader("⚙️ Manage Existing Records")
        if not df.empty:
            target = st.selectbox("Select Vehicle to Edit/Delete", df['plate'].unique())
            v_row = df[df['plate'] == target].iloc[0]
            
            # --- EDIT SECTION ---
            with st.expander(f"📝 Edit Details for {target}"):
                new_driver = st.text_input("Update Driver Name", value=v_row['driver']).upper()
                new_odo = st.number_input("Correction: Odometer Reading", value=int(v_row['odo']))
                if st.button("Update Vehicle Details"):
                    supabase.table("vehicles").update({"driver": new_driver, "odo": new_odo}).eq("plate", target).execute()
                    st.success("Updated!"); st.rerun()
            
            # --- DELETE SECTION ---
            st.divider()
            confirm = st.checkbox(f"⚠️ Confirm PERMANENT DELETE of {target}")
            if st.button(f"🗑️ Delete {target}", disabled=not confirm):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.warning("Vehicle Deleted."); st.rerun()

# --- 5. DRIVER PORTAL (TRIP-SPECIFIC MILEAGE) ---
else:
    st.title(f"👋 Driver: {st.session_state.user}")
    v_data = df[df['driver'].str.upper() == st.session_state.user].iloc[0]
    
    st.info(f"Bus: {v_data['plate']} | Last Recorded Odo: {v_data['odo']} KM")

    with st.form("trip_log"):
        st.write("### Trip Performance Entry")
        new_odo = st.number_input("Current Odometer", min_value=int(v_data['odo']))
        diesel_added = st.number_input("Diesel Filled Now (Liters)", min_value=0.0)
        
        if st.form_submit_button("Calculate Trip Mileage & Save"):
            km_run = new_odo - v_data['odo']
            
            if diesel_added > 0:
                # Calculate mileage for THIS trip specifically
                trip_mileage = round(km_run / diesel_added, 2)
                st.success(f"📊 TRIP REPORT: You ran {km_run} KM on {diesel_added}L. Mileage: {trip_mileage} KM/L")
                
                # RESET trip data for the next cycle
                supabase.table("vehicles").update({
                    "odo": int(new_odo),
                    "trip_km": 0, 
                    "fuel_liters": 0.0 
                }).eq("plate", v_data['plate']).execute()
            else:
                # Regular update if no fuel was added
                supabase.table("vehicles").update({
                    "odo": int(new_odo),
                    "trip_km": int(v_data['trip_km'] + km_run)
                }).eq("plate", v_data['plate']).execute()
                st.info(f"Odometer updated. You have run {v_data['trip_km'] + km_run} KM since your last fuel fill.")
            
            st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
