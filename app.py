import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# --- 1. INITIALIZE ENGINE (Fixes NameError) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Akshara Fleet Tracker", layout="wide")

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.title("Akshara Fleet")
role = st.sidebar.radio("Identify Role", ["📝 Driver Log", "🔐 Manager Dashboard"])

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #4B5563;'>R.G ROAD GANGAVATHI</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- 3. DRIVER LOG PAGE ---
if role == "📝 Driver Log":
    st.header("Daily Fuel & Meter Log")
    try:
        # Get driver list from 'vehicles' table
        v_res = supabase.table("vehicles").select("driver, plate").execute()
        v_df = pd.DataFrame(v_res.data)
        
        if not v_df.empty:
            options = [f"{r['driver']} ({r['plate']})" for _, r in v_df.iterrows()]
            with st.form("log_form", clear_on_submit=True):
                choice = st.selectbox("Select Your Name", options)
                curr_odo = st.number_input("Odometer Reading (KM)", min_value=0)
                curr_fuel = st.number_input("Diesel Added (Liters)", min_value=0.0)
                
                if st.form_submit_button("Submit Log"):
                    d_name = choice.split(" (")[0]
                    p_no = choice.split("(")[1].replace(")", "")
                    
                    # SAVE TO BOTH TABLES
                    supabase.table("fuel_logs").insert({"plate": p_no, "driver": d_name, "odo": curr_odo, "liters": curr_fuel}).execute()
                    supabase.table("vehicles").update({"odo": curr_odo, "fuel_liters": curr_fuel}).eq("plate", p_no).execute()
                    
                    st.success("✅ Log saved successfully!")
                    if curr_fuel > 0:
                        st.metric("Estimated Mileage", f"{(curr_odo/curr_fuel):.2f} KM/L")
        else:
            st.info("No drivers enrolled yet.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- 4. MANAGER DASHBOARD ---
else:
    if "auth" not in st.session_state: st.session_state.auth = False
    
    if not st.session_state.auth:
        pwd = st.text_input("Manager Password", type="password")
        if st.button("Login"):
            if pwd == "Akshara@2026": 
                st.session_state.auth = True
                st.rerun()
            else: st.error("Wrong Password")
    else:
        st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"auth": False}))
        tab1, tab2 = st.tabs(["📈 History & Expenses", "➕ Enrollment"])
        
        with tab1:
            # FETCH HISTORY
            h_res = supabase.table("fuel_logs").select("*").execute()
            h_df = pd.DataFrame(h_res.data)
            
            if not h_df.empty:
                h_df['mileage'] = h_df['odo'] / h_df['liters']
                h_df['date'] = pd.to_datetime(h_df['created_at']).dt.date
                
                # CHART
                fig = px.line(h_df, x="date", y="mileage", color="plate", title="Mileage Trends (KM/L)")
                st.plotly_chart(fig, use_container_width=True)
                
                # EXPENSE CALCULATOR
                st.markdown("---")
                st.header("💰 Monthly Expense Calculator")
                f_price = st.number_input("Diesel Price (₹/L)", value=90.0)
                total_cost = h_df['liters'].sum() * f_price
                st.metric("Total Monthly Diesel Cost", f"₹ {total_cost:,.2f}")
            else:
                st.info("No logs found yet.")

        with tab2:
            with st.form("enroll"):
                p = st.text_input("Plate No")
                d = st.text_input("Driver Name")
                if st.form_submit_button("Enroll Driver"):
                    supabase.table("vehicles").insert({"plate": p, "driver": d, "odo": 0, "fuel_liters": 0}).execute()
                    st.success("Driver Enrolled!")
                    st.rerun()
