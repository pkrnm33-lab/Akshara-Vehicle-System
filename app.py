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
        # Pull fresh data from your project: klvniiwgwyqkvzfbtqa
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. LOGIN GATE (FIXED) ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
    st.subheader("Login Portal")
    user_input = st.text_input("Username (Enter Manager or your Driver Name)").upper().strip()
    
    if st.button("Login"):
        if user_input == "MANAGER":
            st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
        # Checks if the name exists in the database
        elif not df.empty and user_input in df['driver'].str.upper().str.strip().values:
            st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
        else:
            st.error(f"User '{user_input}' not found. Manager must add you to the fleet first.")
    st.stop()

# --- 4. MANAGER DASHBOARD (WITH EDIT/DELETE) ---
if st.session_state.role == "manager":
    st.title("🏆 Manager Dashboard")
    tab1, tab2, tab3 = st.tabs(["Fleet Performance", "Enroll Vehicle", "Manage & Delete"])

    with tab1:
        st.subheader("All Vehicle Status")
        if not df.empty:
            st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Add New Vehicle")
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save Vehicle"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success(f"Driver {d_n} can now log in!"); st.rerun()

    with tab3:
        st.subheader("⚙️ Edit/Delete Vehicles")
        if not df.empty:
            target = st.selectbox("Select Plate No", df['plate'].unique())
            v_row = df[df['plate'] == target].iloc[0]
            
            with st.expander("📝 Edit Driver or Odometer"):
                edit_name = st.text_input("New Driver Name", value=v_row['driver']).upper()
                edit_odo = st.number_input("Odometer Correction", value=int(v_row['odo']))
                if st.button("Update"):
                    supabase.table("vehicles").update({"driver": edit_name, "odo": edit_odo}).eq("plate", target).execute()
                    st.success("Record Updated!"); st.rerun()
            
            st.divider()
            confirm = st.checkbox(f"Permanently Delete {target}?")
            if st.button("🗑️ Delete Now", disabled=not confirm):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.warning("Vehicle Removed."); st.rerun()

# --- 5. DRIVER PORTAL (TRIP MILEAGE) ---
else:
    st.title(f"👋 Driver: {st.session_state.user}")
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    st.info(f"Bus: {v_data['plate']} | Current Odo: {v_data['odo']} KM")

    with st.form("driver_form"):
        new_odo = st.number_input("New Odometer Reading", min_value=int(v_data['odo']))
        diesel = st.number_input("Diesel Filled Now (Liters)", min_value=0.0)
        
        if st.form_submit_button("Submit & Calculate Mileage"):
            km_run = new_odo - v_data['odo']
            
            if diesel > 0:
                # Precise trip mileage calculation
                trip_mileage = round(km_run / diesel, 2)
                st.success(f"✅ TRIP MILEAGE: {trip_mileage} KM/L (Ran {km_run} KM on {diesel}L)")
                
                # Reset trip counters for fresh next-trip calculation
                supabase.table("vehicles").update({
                    "odo": int(new_odo), "trip_km": 0, "fuel_liters": 0.0 
                }).eq("plate", v_data['plate']).execute()
            else:
                supabase.table("vehicles").update({
                    "odo": int(new_odo), "trip_km": int(v_data['trip_km'] + km_run)
                }).eq("plate", v_data['plate']).execute()
                st.info(f"Odo updated. Total KM since last fuel: {v_data['trip_km'] + km_run}")
            
            st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
