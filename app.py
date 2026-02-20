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
        # Pulls live data from your project: klvniiwgwyqkvzfbtqa
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
    t1, t2, t3 = st.tabs(["Fleet Status", "Enroll Vehicle", "Edit & Delete"])
    
    with t1:
        if not df.empty:
            st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters']], use_container_width=True, hide_index=True)
    
    with t2:
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save to Cloud"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("Successfully Enrolled!"); st.rerun()
            
    with t3:
        if not df.empty:
            target = st.selectbox("Select Vehicle", df['plate'].unique())
            v_row = df[df['plate'] == target].iloc[0]
            with st.expander(f"Edit {target}"):
                new_d = st.text_input("Driver", value=v_row['driver']).upper()
                new_o = st.number_input("Odo", value=int(v_row['odo']))
                if st.button("Update"):
                    supabase.table("vehicles").update({"driver": new_d, "odo": new_o}).eq("plate", target).execute()
                    st.rerun()
            st.divider()
            if st.checkbox(f"Delete {target}?"):
                if st.button("Confirm Delete"):
                    supabase.table("vehicles").delete().eq("plate", target).execute()
                    st.rerun()

# --- 5. DRIVER INTERFACE (FIXED TRIP CALCULATION) ---
else:
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    # LARGE DASHBOARD
    st.write("Trip KM")
    st.title(f"{v_data['trip_km']} km")
    
    # This shows mileage using the LAST stored fuel amount
    st.write("Particular Mileage (Last Trip)")
    last_m = round(v_data['trip_km'] / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    st.title(f"{last_m} km/l")
    
    st.divider()

    # STEP 1: DAILY ODO UPDATE
    st.write("Update Odometer (End of Day)")
    new_odo = st.number_input("Odo", min_value=float(v_data['odo']), value=float(v_data['odo']), label_visibility="collapsed")
    if st.button("Save Daily Run"):
        km_today = new_odo - v_data['odo']
        # Update Total Odometer and Trip KM
        supabase.table("vehicles").update({
            "odo": int(new_odo),
            "trip_km": int(v_data['trip_km'] + km_today)
        }).eq("plate", v_data['plate']).execute()
        st.success(f"Today's Run: {km_today} KM added to Trip."); st.rerun()

    st.divider()

    # STEP 2: MILEAGE CALC & RESET
    st.write("Diesel Refilled Now (Liters)")
    diesel = st.number_input("Diesel Liters", min_value=0.0, value=0.0, label_visibility="collapsed")
    
    if st.button("Log Fuel & Calculate Mileage"):
        if diesel > 0 and v_data['trip_km'] > 0:
            # 1. Calculate trip-specific mileage
            trip_m = round(v_data['trip_km'] / diesel, 2)
            
            # 2. Update the record with this specific fuel amount
            supabase.table("vehicles").update({"fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            
            st.success(f"✅ TRIP COMPLETE! Mileage: {trip_m} km/l")
            st.info(f"You ran {v_data['trip_km']} KM on {diesel}L.")
            
            # 3. Reset Trip KM for the NEXT tank fill
            if st.button("Start New Trip Cycle"):
                supabase.table("vehicles").update({"trip_km": 0}).eq("plate", v_data['plate']).execute()
                st.rerun()
            st.balloons()
        else:
            st.error("Enter liters and ensure Trip KM > 0.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
