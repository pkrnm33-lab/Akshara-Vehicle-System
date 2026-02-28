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
    try: v_data = supabase.table("vehicles").select("*").execute().data
    except: v_data = []
    try: l_data = supabase.table("logs").select("*").execute().data
    except: l_data = []
    try: m_data = supabase.table("maintenance").select("*").execute().data
    except: m_data = []
    
    try:
        supabase.table("backups").insert({
            "backup_date": today_str, "event_type": event_name,
            "vehicles_data": json.dumps(v_data), "logs_data": json.dumps(l_data)
        }).execute()
    except: pass 

# --- 4. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.markdown('<div style="background-color:#FFD700;padding:15px;border-radius:15px;margin-bottom:20px;"><h1 style="color:#000080;text-align:center;">🚌 AKSHARA PUBLIC SCHOOL</h1></div>', unsafe_allow_html=True)
    user_input = st.text_input("👤 Enter Username").upper().strip()
    
    if user_input == "MANAGER":
        password = st.text_input("🔐 Manager Password", type="password")
        if st.button("Login as Manager"):
            if password == "Akshara@2026": 
                st.session_state.role = "manager"; st.session_state.logged_in = True
                today_date = datetime.now().strftime("%Y-%m-%d")
                backups_df = load_data("backups")
                if backups_df.empty or not backups_df['backup_date'].astype(str).str.contains(today_date).any():
                    trigger_auto_backup("Daily Auto-Backup")
                st.rerun()
            else:
                st.error("❌ Invalid Password")
    else:
        if st.button("Login as Driver"):
            if not df.empty and 'driver' in df.columns and user_input in df['driver'].str.upper().str.strip().values:
                st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
            else:
                st.error("❌ Driver not found in fleet.")
    st.stop()

# --- 5. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    st.markdown('<h2 style="color:#000080;text-align:center;">🏆 Manager Dashboard</h2>', unsafe_allow_html=True)
    
    t1, t2, t3, t4, t5, t6 = st.tabs(["📊 Live", "📅 Monthly", "🔧 Maintenance", "✏️ Corrections", "☁️ Backups", "🚨 DANGER"])
    
    # 1. LIVE FLEET
    with t1:
        if not df.empty and 'plate' in df.columns:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            m_df['Mileage'] = m_df['Mileage'].astype(float).round(2)
            def style_mileage(v): return 'color: green; font-weight: bold' if v > 12 else 'color: red'
            
            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']].style.map(style_mileage, subset=['Mileage']), use_container_width=True, hide_index=True)
        else:
            st.info("Fleet is empty. Please add a vehicle.")
    
    # 2. MONTHLY SHEET
    with t2:
        st.subheader("📅 Monthly Diesel Sheet")
        logs_df = load_data("logs")
        if not logs_df.empty and 'date' in logs_df.columns:
            logs_df['date'] = pd.to_datetime(logs_df['date'], errors='coerce')
            logs_df = logs_df.dropna(subset=['date']) 
            logs_df['Month_Year'] = logs_df['date'].dt.strftime('%B %Y')
            
            available_months = logs_df['Month_Year'].unique().tolist()
            if available_months:
                selected_month = st.selectbox("🎯 Select Month to View:", available_months)
                filtered_logs = logs_df[logs_df['Month_Year'] == selected_month]
                
                if not filtered_logs.empty:
                    grand_total_cost = filtered_logs['total_cost'].sum() if 'total_cost' in filtered_logs.columns else 0
                    grand_total_liters = filtered_logs['liters'].sum()
                    grand_total_km = filtered_logs['km_run'].sum() if 'km_run' in filtered_logs.columns else 0
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("💰 Total Cost", f"₹ {grand_total_cost:,.2f}")
                    c2.metric("🛢️ Total Diesel", f"{grand_total_liters:,.2f} L")
                    c3.metric("🛣️ Total KM Run", f"{grand_total_km} km")
                    st.divider()

                    report = filtered_logs.groupby(['plate', 'driver']).agg(
                        Total_KM=('km_run', 'sum'),
                        Total_Liters=('liters', 'sum'),
                        Total_Cost=('total_cost', 'sum')
                    ).reset_index()
                    
                    report['Monthly Mileage'] = report.apply(lambda x: round(x['Total_KM'] / x['Total_Liters'], 2) if x['Total_Liters'] > 0 else 0, axis=1)
                    report.rename(columns={'Total_KM': 'Total KM', 'Total_Liters': 'Total Diesel (L)', 'Total_Cost': 'Total Cost (₹)'}, inplace=True)
                    
                    display_cols = ['plate', 'driver', 'Total KM', 'Total Diesel (L)', 'Monthly Mileage', 'Total Cost (₹)']
                    st.dataframe(report[display_cols], use_container_width=True, hide_index=True)
                    
                    csv = report[display_cols].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download This Month", data=csv, file_name=f"Akshara_Fleet_{selected_month}.csv", mime="text/csv")
            else:
                st.info("No valid dates found in logs.")
        else:
            st.info("No fuel logs recorded yet.")

    # 3. MAINTENANCE (UPGRADED DASHBOARD)
    with t3:
        st.subheader("🔧 Maintenance & Repairs Log")
        with st.expander("➕ Log New Repair or Service"):
            if not df.empty and 'plate' in df.columns:
                m_plate = st.selectbox("Select Bus", df['plate'].unique(), key="maint_plate")
                current_v_odo = int(df[df['plate'] == m_plate]['odo'].values[0])
                
                c1, c2 = st.columns(2)
                m_date = c1.date_input("Date of Service", datetime.today()) 
                m_type = c2.selectbox("Type of Work", ["Oil Change", "Mechanical Repair", "Electrical Repair", "Tyre Replacement", "Body Work", "Other"])
                
                c3, c4 = st.columns(2)
                m_cost = c3.number_input("Total Repair Bill (₹)", min_value=0.0, value=0.0)
                m_odo = c4.number_input("Odometer at time of service", value=current_v_odo)
                
                m_notes = st.text_input("Details (e.g., Replaced battery, Engine oil brand)")
                
                if st.button("Save Maintenance Record"):
                    supabase.table("maintenance").insert({
                        "plate": m_plate, "date": m_date.strftime("%Y-%m-%d"), "work_type": m_type,
                        "cost": float(m_cost), "notes": m_notes, "odo": int(m_odo)
                    }).execute()
                    st.success("Repair Logged!"); st.rerun()
            else:
                st.info("No vehicles in the fleet to log maintenance for.")
        
        st.divider()
        st.write("### 📜 Fleet Maintenance Dashboard")
        maint_df = load_data("maintenance")
        
        if not maint_df.empty and 'cost' in maint_df.columns:
            # A. Grand Total Maintenance Metric
            grand_total_maint = maint_df['cost'].sum()
            st.metric("🛠️ Total Fleet Maintenance Cost", f"₹ {grand_total_maint:,.2f}")
            
            # B. Vehicle-Wise Maintenance Sheet
            st.write("#### 🚌 Vehicle-Wise Maintenance Sheet")
            maint_summary = maint_df.groupby('plate').agg(
                Total_Repairs=('work_type', 'count'),
                Total_Cost=('cost', 'sum')
            ).reset_index()
            
            maint_summary.rename(columns={'plate': 'Plate No', 'Total_Repairs': 'Number of Services', 'Total_Cost': 'Total Cost (₹)'}, inplace=True)
            maint_summary = maint_summary.sort_values(by="Total Cost (₹)", ascending=False)
            
            st.dataframe(maint_summary, use_container_width=True, hide_index=True)
            
            csv_maint_sum = maint_summary.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Summary Sheet", data=csv_maint_sum, file_name="Akshara_Maintenance_Summary.csv", mime="text/csv")
            
            st.divider()
            
            # C. Detailed History
            st.write("#### 🧾 Detailed Repair History")
            st.dataframe(maint_df[['date', 'plate', 'work_type', 'cost', 'notes', 'odo']].sort_values(by="date", ascending=False), use_container_width=True, hide_index=True)
            
            csv_maint_hist = maint_df[['date', 'plate', 'work_type', 'cost', 'notes', 'odo']].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Detailed History", data=csv_maint_hist, file_name="Akshara_Maintenance_History.csv", mime="text/csv")
        else:
            st.info("No maintenance records logged yet.")

    # 4. MANAGER CORRECTION CENTER
    with t4:
        st.subheader("✏️ Data Correction Center")
        
        # A. Edit Fleet 
        with st.expander("🚌 Manage Fleet (Add / Edit / Delete Buses)"):
            action = st.radio("Action:", ["Add New Bus", "Edit Driver Name", "Delete Bus"], horizontal=True)
            if action == "Add New Bus":
                p_n = st.text_input("Plate No").upper().strip()
                d_n = st.text_input("Driver Name").upper().strip()
                start_meter = st.number_input("Starting Odometer (VERY IMPORTANT)", min_value=0, value=0)
                
                if st.button("Save to Fleet"):
                    supabase.table("vehicles").upsert({
                        "plate": p_n, "driver": d_n, "odo": int(start_meter), 
                        "trip_km": int(start_meter), "fuel_liters": 0.0
                    }).execute()
                    st.success("Added with correct starting meter!"); st.rerun()
            elif action == "Edit Driver Name":
                if not df.empty and 'plate' in df.columns:
                    target_edit = st.selectbox("Select Bus", df['plate'].unique(), key="edit_driver")
                    curr_driver = df[df['plate'] == target_edit]['driver'].values[0]
                    new_driver = st.text_input("Update Driver", value=curr_driver).upper().strip()
                    if st.button("Update Driver"):
                        supabase.table("vehicles").update({"driver": new_driver}).eq("plate", target_edit).execute()
                        st.success("Updated!"); st.rerun()
                else:
                    st.info("No buses available to edit.")
            elif action == "Delete Bus":
                if not df.empty and 'plate' in df.columns:
                    target_del = st.selectbox("Select Bus", df['plate'].unique(), key="del_bus")
                    if st.button("Delete Permanently"):
                        supabase.table("vehicles").delete().eq("plate", target_del).execute()
                        st.success("Deleted!"); st.rerun()
                else:
                    st.info("No buses available to delete.")

        # B. Correct Live Odometer
        with st.expander("⏱️ Correct a Live Odometer"):
            if not df.empty and 'plate' in df.columns:
                target_odo = st.selectbox("Select Bus", df['plate'].unique(), key="edit_odo")
                curr_odo = df[df['plate'] == target_odo]['odo'].values[0]
                new_odo_val = st.number_input("Correct Odometer Reading", value=int(curr_odo))
                if st.button("Force Update Odometer"):
                    supabase.table("vehicles").update({"odo": int(new_odo_val)}).eq("plate", target_odo).execute()
                    st.success("Odometer Corrected!"); st.rerun()
            else:
                st.info("No vehicles currently in the fleet.")

        # C. Correct Fuel Logs
        with st.expander("⛽ Correct a Past Fuel Fill-up Log"):
            c_logs_df = load_data("logs")
            if not c_logs_df.empty and 'id' in c_logs_df.columns:
                c_logs_df['label'] = c_logs_df['date'].astype(str) + " | " + c_logs_df['plate'] + " | " + c_logs_df['liters'].astype(str) + "L"
                log_map = dict(zip(c_logs_df['label'], c_logs_df['id']))
                
                selected_log_label = st.selectbox("Select Fuel Entry to Fix", c_logs_df['label'].tolist())
                selected_log_id = log_map[selected_log_label]
                log_data = c_logs_df[c_logs_df['id'] == selected_log_id].iloc[0]
                
                c1, c2, c3 = st.columns(3)
                fix_km = c1.number_input("Fix KM Run", value=int(log_data['km_run']))
                fix_liters = c2.number_input("Fix Liters", value=float(log_data['liters']))
                fix_rate = c3.number_input("Fix Rate (₹)", value=float(log_data.get('rate_per_ltr', 0.0)))
                
                if st.button("Update Fuel Record"):
                    new_mileage = round(fix_km / fix_liters, 2) if fix_liters > 0 else 0
                    new_cost = fix_liters * fix_rate
                    supabase.table("logs").update({
                        "km_run": fix_km, "liters": fix_liters, "rate_per_ltr": fix_rate,
                        "mileage": new_mileage, "total_cost": new_cost
                    }).eq("id", int(selected_log_id)).execute()
                    st.success("Fuel Log Corrected! Monthly sheet updated."); st.rerun()
                
                if st.button("🗑️ Delete this Fuel Entry"):
                    supabase.table("logs").delete().eq("id", int(selected_log_id)).execute()
                    st.success("Entry Deleted!"); st.rerun()
            else:
                st.info("No fuel logs available to correct.")

        # D. Correct Maintenance
        with st.expander("🔧 Correct a Maintenance Record"):
            c_maint_df = load_data("maintenance")
            if not c_maint_df.empty and 'id' in c_maint_df.columns:
                c_maint_df['label'] = c_maint_df['date'].astype(str) + " | " + c_maint_df['plate'] + " | " + c_maint_df['work_type']
                maint_map = dict(zip(c_maint_df['label'], c_maint_df['id']))
                
                selected_m_label = st.selectbox("Select Repair Entry to Fix", c_maint_df['label'].tolist())
                selected_m_id = maint_map[selected_m_label]
                m_data = c_maint_df[c_maint_df['id'] == selected_m_id].iloc[0]
                
                fix_m_cost = st.number_input("Fix Cost (₹)", value=float(m_data['cost']))
                fix_m_notes = st.text_input("Fix Notes", value=str(m_data['notes']))
                
                if st.button("Update Maintenance Record"):
                    supabase.table("maintenance").update({
                        "cost": fix_m_cost, "notes": fix_m_notes
                    }).eq("id", int(selected_m_id)).execute()
                    st.success("Repair Corrected!"); st.rerun()
                
                if st.button("🗑️ Delete this Repair Entry"):
                    supabase.table("maintenance").delete().eq("id", int(selected_m_id)).execute()
                    st.success("Repair Deleted!"); st.rerun()
            else:
                st.info("No maintenance records available to correct.")

    # 5. BACKUPS & 6. DANGER
    with t5:
        st.subheader("☁️ Auto-Backup Archive")
        backups_df = load_data("backups")
        if not backups_df.empty: st.dataframe(backups_df[['id', 'backup_date', 'event_type']].sort_values(by="id", ascending=False), use_container_width=True, hide_index=True)
    
    with t6:
        st.error("⚠️ MASTER RESET - FACTORY WIPE")
        st.write("This will permanently erase ALL vehicles, ALL monthly fuel logs, and ALL maintenance history.")
        confirm_reset = st.text_input("Type 'RESET ALL' to confirm your action:")
        
        if st.button("🚨 ERASE ENTIRE SYSTEM"):
            if confirm_reset == "RESET ALL":
                trigger_auto_backup("Emergency Backup before Factory Wipe")
                
                if not df.empty and 'plate' in df.columns:
                    for p in df['plate'].unique(): 
                        supabase.table("vehicles").delete().eq("plate", p).execute()
                
                logs_df_wipe = load_data("logs")
                if not logs_df_wipe.empty and 'id' in logs_df_wipe.columns:
                    for l_id in logs_df_wipe['id'].unique():
                        supabase.table("logs").delete().eq("id", int(l_id)).execute()
                        
                maint_df_wipe = load_data("maintenance")
                if not maint_df_wipe.empty and 'id' in maint_df_wipe.columns:
                    for m_id in maint_df_wipe['id'].unique():
                        supabase.table("maintenance").delete().eq("id", int(m_id)).execute()

                st.success("FACTORY RESET COMPLETE! Live data, Monthly sheets, and Maintenance are all completely empty.")
                st.rerun()
            else:
                st.error("You must type 'RESET ALL' exactly in the box above before clicking the button.")

# --- 6. DRIVER INTERFACE ---
else:
    st.markdown(f'<h2 style="color:#000080;text-align:center;">👋 Welcome, {st.session_state.user}</h2>', unsafe_allow_html=True)
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    if trip_dist > 5000:
        st.warning("⚠️ Trip distance looks unusually high! Did you type the odometer correctly?")
    
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
    rate = st.number_input("Rate per Liter (₹)", min_value=0.0, value=0.0)
    
    if st.button("Log Fuel & Start New Trip"):
        if diesel > 0 and rate > 0:
            try:
                log_payload = {
                    "plate": v_data['plate'], "driver": v_data['driver'], "km_run": int(trip_dist),
                    "liters": float(diesel), "mileage": float(round(trip_dist / diesel, 2)),
                    "rate_per_ltr": float(rate), "total_cost": float(diesel * rate),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                try: log_payload["odo"] = int(v_data['odo']) 
                except: pass
                
                supabase.table("logs").insert(log_payload).execute()
            except Exception as e:
                st.error("Error saving log. Check your database columns.")
                
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            st.success(f"Fuel logged! Total Cost: ₹{diesel * rate}"); st.rerun()
        else:
            st.error("Please enter both Liters and the Rate per Liter.")

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
