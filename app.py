import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. BRANDING & LOGO ---
LOGO_IMAGE = "1000000180.jpg" 

st.set_page_config(page_title="Akshara Fleet Portal", page_icon="🚌")

# --- 2. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Check Streamlit Secrets.")
    st.stop()

# --- 3. HIGH-VISIBILITY DARK STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117 !important; }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: #FFFFFF !important; }}
    .branded-header {{
        border-bottom: 4px solid #4CAF50;
        padding: 10px 0 20px 0;
        margin-bottom: 30px;
        text-align: center;
        background-color: #1A1C24;
    }}
    div[data-testid="stMetric"] {{
        background: #1A1C24 !important;
        border: 1px solid #4CAF50 !important;
        border-radius: 12px;
        padding: 15px;
    }}
    div[data-testid="stMetricValue"] > div {{ color: #FFFFFF !important; font-weight: 800 !important; }}
    div.stButton > button {{
        background-color: #2E7D32 !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        font-weight: 700;
        padding: 12px 20px;
        width: 100%;
    }}
    .reset-btn button {{ background-color: #FFD700 !important; color: #000000 !important; }}
    /* Custom Styling for the Total Expenditure Highlight */
    .total-card {{
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #FFD700;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA LOADER ---
def load_data():
    try:
        # Fetching current vehicle status and the fuel log history
        v_res = supabase.table("vehicles").select("*").execute()
        f_res = supabase.table("fuel_logs").select("*").execute()
        return pd.DataFrame(v_res.data), pd.DataFrame(f_res.data)
    except:
        return pd.DataFrame(), pd.DataFrame()

df_v, df_f = load_data()

# --- 5. SHARED HEADER ---
def draw_header(title=""):
    st.markdown('<div class="branded-header">', unsafe_allow_html=True)
    try:
        st.image(LOGO_IMAGE, width=250)
    except:
        st.markdown('<h1 style="color:#FFFFFF;">AKSHARA PUBLIC SCHOOL</h1>', unsafe_allow_html=True)
    if title:
        st.markdown(f'<h2 style="color:#4CAF50; font-size:22px;">{title}</h2>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    draw_header("FLEET LOGIN")
    user_input = st.text_input("Username").upper().strip()
    if user_input == "MANAGER":
        password = st.text_input("Password", type="password")
        if st.button("Login as Manager"):
            if password == "Akshara@2026": 
                st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
            else: st.error("Invalid Password")
    else:
        if st.button("Login as Driver"):
            if not df_v.empty and user_input in df_v['driver'].str.upper().str.strip().values:
                st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
            else: st.warning("Driver not found.")
    st.stop()

# --- 7. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    draw_header("🏆 MANAGER PORTAL")
    t1, t2, t3 = st.tabs(["📊 Performance", "➕ Add Vehicle", "📜 Fuel History"])
    
    with t1:
        if not df_f.empty:
            # Calculate Total Expenditure for the entire fleet
            df_f['Cost'] = df_f['liters'] * df_f['price']
            total_spent = df_f['Cost'].sum()
            
            st.markdown(f"""
                <div class="total-card">
                    <h3 style="margin:0; color:#FFD700;">💰 TOTAL FLEET EXPENDITURE</h3>
                    <h1 style="margin:0; color:#FFFFFF;">₹ {total_spent:,.2f}</h1>
                </div>
            """, unsafe_allow_html=True)
            
            # Group data by plate to show per-vehicle totals
            summary = df_f.groupby('plate').agg({
                'liters': 'sum',
                'Cost': 'sum'
            }).reset_index()
            
            st.write("### 🏎️ Per-Vehicle Summary")
            st.dataframe(summary.rename(columns={'liters': 'Total Diesel (L)', 'Cost': 'Total Spent (₹)'}), 
                         use_container_width=True, hide_index=True)

    with t2:
        st.subheader("Enroll New Vehicle")
        p_n = st.text_input("Plate Number").upper().strip()
        d_n = st.text_input("Driver Name").upper().strip()
        if st.button("Save to System"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0}).execute()
            st.success(f"Vehicle {p_n} added!"); st.rerun()

    with t3:
        st.subheader("Full Fuel Log")
        if not df_f.empty:
            st.dataframe(df_f.sort_values('created_at', ascending=False), use_container_width=True, hide_index=True)
            st.download_button("📥 Export History", data=df_f.to_csv(index=False), file_name="fuel_history.csv")

# --- 8. DRIVER INTERFACE ---
else:
    draw_header(f"Welcome, {st.session_state.user}")
    v_data = df_v[df_v['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    
    st.subheader("1. Update Daily Reading")
    new_odo = st.number_input("Current Odometer", min_value=float(v_data['odo']), value=float(v_data['odo']))
    if st.button("Save Reading"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.success("Odometer Updated!"); st.rerun()

    st.divider()
    st.subheader("2. Diesel Refilled")
    col_a, col_b = st.columns(2)
    with col_a:
        diesel = st.number_input("Liters Added", min_value=0.0)
    with col_b:
        price = st.number_input("Price per Liter (₹)", min_value=0.0, value=100.0)
    
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Log Fuel & Add to History"):
        if diesel > 0:
            # 1. Update the vehicle's current trip status
            supabase.table("vehicles").update({"trip_km": int(v_data['odo'])}).eq("plate", v_data['plate']).execute()
            
            # 2. ADD a new record to the fuel_logs table (This prevents erasing data)
            supabase.table("fuel_logs").insert({
                "plate": v_data['plate'],
                "driver": st.session_state.user,
                "liters": float(diesel),
                "price": float(price)
            }).execute()
            
            st.success("Fuel Logged Successfully!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()
