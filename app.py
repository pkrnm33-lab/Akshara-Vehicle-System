import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- 1. SECURE DATABASE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ DATABASE CONNECTION FAILED")
    st.info("Check your Streamlit Secrets for project ID: klvniiwgwyqkvzfbtqa")
    st.stop()

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="Akshara Vehicle System", layout="centered", page_icon="🚌")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Vehicle Maintenance & Fuel Log</h4>", unsafe_allow_html=True)
st.divider()

# Load fresh data from Supabase vehicles table
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 3. MANAGER DASHBOARD (Fleet Setup) ---
with st.sidebar:
    st.header("🛠️ Admin Controls")
    with st.expander("Enroll New Vehicle"):
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Add to Fleet"):
            if p_n and d_n:
                supabase.table("vehicles").insert({
                    "plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0
                }).execute()
                st.success(f"Enrolled {d_n}!"); st.rerun()
    
    st.divider()
    # Fuel Price setting for financial reports
    fuel_price = st.number_input("Current Diesel Price (₹/L)", min_value=0.0, value=90.0)

# --- 4. LIVE FLEET STATUS ---
if not df.empty:
    st.subheader("Live Fleet Status")
    # Clean data for display
    status_df = df[['plate', 'driver', 'odo', 'trip_km']].copy()
    status_df.columns = ['PLATE', 'DRIVER', 'ODOMETER (KM)', 'TOTAL TRIP']
    st.dataframe(status_df, use_container_width=True, hide_index=True)
    st.divider()

# --- 5. DRIVER LOGGING FORM ---
st.subheader("Daily Fuel & Meter Log")
if not df.empty:
    driver_options = [f"{row['driver']} ({row['plate']})" for _, row in df.iterrows()]
    selected_option = st.selectbox("Select Your Name", driver_options)
    
    selected_plate = selected_option.split("(")[1].replace(")", "")
    v_data = df[df['plate'] == selected_plate].iloc[0]

    with st.form("log_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_odo = st.number_input("Current Odometer (KM)", min_value=int(v_data['odo']), step=1)
        with col2:
            diesel = st.number_input("Diesel Added (Liters)", min_value=0.0, step=0.1)
        
        if st.form_submit_button("Submit Log"):
            diff = new_odo - v_data['odo']
            try:
                supabase.table("vehicles").update({
                    "odo": int(new_odo),
                    "trip_km": int(v_data['trip_km'] + diff),
                    "fuel_liters": float(v_data['fuel_liters'] + diesel)
                }).eq("plate", selected_plate).execute()
                
                st.success("✅ Log saved successfully!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("No vehicles enrolled. Use the sidebar to add drivers.")

# --- 6. MONTHLY REPORT & ANALYTICS ---
if not df.empty:
    st.divider()
    st.subheader("📊 Management Reports")
    
    # Calculate costs
    report_df = df[['plate', 'driver', 'trip_km', 'fuel_liters']].copy()
    report_df['Total Cost (₹)'] = report_df['fuel_liters'] * fuel_price
    report_df.columns = ['Plate No', 'Driver', 'Monthly KM', 'Total Diesel (L)', 'Fuel Cost (₹)']
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Total Fleet KM", f"{report_df['Monthly KM'].sum()} km")
    with col_b:
        st.metric("Total Fuel Cost", f"₹{report_df['Fuel Cost (₹)'].sum():,.2f}")

    # Export to Excel/CSV
    csv = report_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Excel Report",
        data=csv,
        file_name=f"Akshara_Report_{datetime.now().strftime('%b_%Y')}.csv",
        mime="text/csv"
    )
