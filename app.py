# --- UPDATED DATA LOADER ---
def load_data():
    try:
        v_res = supabase.table("vehicles").select("*").execute()
        v_df = pd.DataFrame(v_res.data)
        
        # Load Fuel Logs
        f_res = supabase.table("fuel_logs").select("*").execute()
        f_df = pd.DataFrame(f_res.data) if f_res.data else pd.DataFrame()
        
        # Load Maintenance Logs
        m_res = supabase.table("maintenance_logs").select("*").execute()
        m_df = pd.DataFrame(m_res.data) if m_res.data else pd.DataFrame()
            
        return v_df, f_df, m_df
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- MANAGER VIEW LOGIC ---
# This merges both costs into your main report
if not df_f.empty:
    fuel_sums = df_f.groupby('plate')['Cost'].sum().reset_index()
    report = report.merge(fuel_sums, on='plate', how='left').fillna(0)
    
if not df_m.empty:
    maint_sums = df_m.groupby('plate')['cost'].sum().reset_index().rename(columns={'cost': 'Maint Cost'})
    report = report.merge(maint_sums, on='plate', how='left').fillna(0)
