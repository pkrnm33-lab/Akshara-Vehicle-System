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
    tab1, tab2, tab3 = st.tabs(["Fleet Status", "Add/Assign Driver", "Reset & Delete"])

    with tab1:
        st.subheader("Live Performance")
        if not df.empty:
            # Mileage = Current Trip KM / Current Trip Diesel
            df['mileage'] = df.apply(lambda x: round(x['trip_km'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            st.dataframe(df[['plate', 'driver', 'odo', 'trip_km', 'fuel_liters', 'mileage']], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Enroll New Vehicle/Driver")
        p_n = st.text_input("Plate No").upper()
        d_n = st.text_input("Driver Name").upper()
        if st.button("Save to Fleet"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("Saved!"); st.rerun()

    with tab3:
        st.subheader("🎯 Precise Reset & Delete")
        if not df.empty:
            target = st.selectbox("Select Vehicle", df['plate'].unique())
            
            st.divider()
            st.write(f"### Options for {target}")
            
            # --- SAFETY LOCK FOR DELETE ---
            confirm_check = st.checkbox(f"I am sure I want to PERMANENTLY DELETE {target}")
            
            col1, col2 = st.columns(2)
            
            if col1.button(f"🗑️ DELETE {target}", disabled=not confirm_check):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.warning(f"Vehicle {target} removed from system.")
                st.rerun()
            
            if col2.button(f"🔄 RESET TRIP DATA for {target}"):
                # Clears trip data for fresh mileage calculation
                supabase.table("vehicles").update({"trip_km": 0, "fuel_liters": 0.0}).eq("plate", target).execute()
                st.success(f"Trip data for {target} cleared!")
                st.rerun()

# --- 5. DRIVER PORTAL ---
else:
    st.title(f"👋 Driver: {st.session_state.user}")
    v_data = df[df['driver'].str.upper() == st.session_state.user].iloc[0]
    
    # Calculate and show trip-specific mileage
    mileage = round(v_data['trip_km'] / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    st.metric("Your Trip Mileage", f"{mileage} KM/L")

    with st.form("log"):
        new_odo = st.number_input("New Odometer", min_value=int(v_data['odo']))
        new_fuel = st.number_input("Diesel Added (L)", min_value=0.0)
        if st.form_submit_button("Submit"):
            diff = new_odo - v_data['odo']
            supabase.table("vehicles").update({
                "odo": int(new_odo), 
                "trip_km": int(v_data['trip_km'] + diff),
                "fuel_liters": float(v_data['fuel_liters'] + new_fuel)
            }).eq("plate", v_data['plate']).execute()
            st.success("Log Saved!"); st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
