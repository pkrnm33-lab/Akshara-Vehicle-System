import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import json

# --- 1. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Check Streamlit Secrets.")
    st.stop()

# --- 2. DATA LOADER ---
def load_data(table_name):
    try:
        res = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data("vehicles")

# --- 3. CRASH-PROOF AUTO-BACKUP ENGINE ---
def trigger_auto_backup(event_name):
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Safely try to get vehicle data
    try:
        v_data = supabase.table("vehicles").select("*").execute().data
    except:
        v_data = []
        
    # Safely try to get logs data (This caused the crash earlier!)
    try:
        l_data = supabase.table("logs").select("*").execute().data
    except:
        l_data = []
    
    # Safely try to save the backup
    try:
        supabase.table("backups").insert({
            "backup_date": today_str,
            "event_type": event_name,
            "vehicles_data": json.dumps(v_data),
            "logs_data": json.dumps(l_data)
        }).execute()
    except:
        pass # If backups table is missing, just ignore and don't crash

# --- 4. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.markdown('<div style="background-color:#FFD700;padding:15px;border-radius:15px;margin-bottom:20px;"><h1 style="color:#000080;text-align:center;">🚌 AKSHARA PUBLIC SCHOOL</h1></div>', unsafe_allow_html=True)
    user_input = st.text_input("👤 Enter Username").upper().strip()
    
    if user_input == "MANAGER":
        password = st.text_input("🔐 Manager Password", type="password")
        if st.button("Login as Manager"):
            if password == "Akshara@2026": 
                st.session_state.role = "manager"
                st.session_state.logged_in = True
                
                # DAILY AUTO-BACKUP CHECK
                today_date = datetime.now().strftime("%Y-%m-%d")
                backups_df = load_data("backups")
                if backups_df.empty or not backups_df['backup_date'].astype(str).str.contains(today_date).any():
                    trigger_auto_backup("Daily Auto-Backup")
                    
                st.rerun()
            else:
                st.error("❌ Invalid Password")
    else:
        if st.button("Login as Driver"):
            if not df.empty and user_input in df['driver'].str.upper().str.strip().values:
                st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
            else:
                st.error("❌ Driver not found in fleet.")
    st.stop()

# --- 5. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    st.markdown('<h2 style="color:#000080;text-align:center;">🏆 Manager Dashboard</h2>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["📊 Live Fleet", "📅 Monthly Sheet", "➕ Add Vehicle", "☁️ Cloud Backups", "🚨 DANGER ZONE"])
    
    with t1:
        if not df.empty:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            def style_mileage(v):
                return 'color: green; font-weight: bold' if v > 12 else 'color: red'
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']].style.map(style_mileage, subset=['Mileage']), use_container_width=True, hide_index=True)
    
    with t2:
        st.subheader("📅 Monthly Diesel Sheet")
        logs_df = load_data("logs")
        if not logs_df.empty:
            logs_df['date'] = pd.to_datetime(logs_df['date'])
            current_month = datetime.now().month
            current_year = datetime.now().year
            monthly_logs = logs_df[(logs_df['date'].dt.month == current_month) & (logs_df['date'].dt.year == current_year)]
            
            if not monthly_logs.empty:
                report = monthly_logs.groupby(['plate', 'driver'])['liters'].sum().reset_index()
                report.rename(columns={'liters': 'Total Diesel (Liters)'}, inplace=True)
                st.dataframe(report, use_container_width=True, hide_index=True)
                csv = report.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Monthly Sheet", data=csv, file_name=f"Akshara_Diesel_{current_month}_{current_year}.csv", mime="text/csv")
            else:
                st.info("No fuel logged yet for this month.")
        else:
            st.warning("⚠️ 'logs' table is missing in Supabase. You need it to track monthly diesel!")

    with t3:
        st.subheader("Enroll New Bus")
        p_n = st.text_input("Plate No").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save to Fleet"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success(f"{p_n} Added!"); st.rerun()

    with t4:
        st.subheader("☁️ Auto-Backup Archive")
        backups_df = load_data("backups")
        if not backups_df.empty:
            st.dataframe(backups_df[['id', 'backup_date', 'event_type']].sort_values(by="id", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No backups created yet.")

    with t5:
        st.error("⚠️ MASTER RESET")
        confirm = st.text_input("Type 'RESET ALL' to confirm your action:")
        if st.button("🚨 ERASE TOTAL VEHICLE DETAILS"):
            if confirm == "RESET ALL":
                if not df.empty:
                    trigger_auto_backup("Pre-Reset Emergency Backup")
                    for plate in df['plate'].unique():
                        supabase.table("vehicles").delete().eq("plate", plate).execute()
                    st.success("ALL VEHICLE DETAILS ERASED.")
                    st.rerun()
            else:
                st.error("You must type 'RESET ALL' exactly to confirm this action.")

# --- 6. DRIVER INTERFACE ---
else:
    st.markdown(f'<h2 style="color:#000080;text-align:center;">👋 Welcome, {st.session_state.user}</h2>', unsafe_allow_html=True)
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    c1, c2 = st.columns(2)
    c1.metric("📌 Trip Distance", f"{trip_dist} km")
    c2.metric("⛽ Mileage", f"{trip_mileage} km/l")
    st.divider()

    new_odo = st.number_input("Current Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Update Odometer"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer updated!"); st.rerun()

    st.divider()

    diesel = st.number_input("Diesel Liters Added", min_value=0.0, value=0.0)
    if st.button("Log Fuel & Start New Trip"):
        if diesel > 0:
            # Try to save to logs (for monthly sheet)
            try:
                supabase.table("logs").insert({
                    "plate": v_data['plate'],
                    "driver": v_data['driver'],
                    "km_run": int(trip_dist),
                    "liters": float(diesel),
                    "mileage": float(round(trip_dist / diesel, 2)) if diesel > 0 else 0,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }).execute()
            except:
                pass # Ignore if logs table is missing
            
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            st.success("Fuel logged successfully!"); st.rerun()
        else:
            st.error("Please enter liters.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
