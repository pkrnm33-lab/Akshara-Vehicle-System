import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SECURE CONNECTION ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ Connection Error. Check Streamlit Secrets.")
    st.stop()

# --- 2. THEME & ULTRA-COLORFUL STYLING ---
st.set_page_config(
    page_title="Akshara Vehicle System",
    page_icon="🚌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Import a nice font */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Main School Header with Sunset Gradient */
    .school-header {
        background: linear-gradient(135deg, #FFD700, #FF8C00); /* Gold to Orange */
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        margin-bottom: 30px;
        text-align: center;
        color: #000080;
    }

    /* Login Container (Bright Blue) */
    .login-container {
        background-color: #e3f2fd; /* Light Blue */
        padding: 35px;
        border-radius: 25px;
        border: 3px solid #2196f3; /* Strong Blue Border */
        box-shadow: 0 4px 12px rgba(33,150,243,0.2);
        text-align: center;
    }

    /* Driver Dashboard Container (Fresh Green) */
    .driver-container {
        background-color: #e8f5e9; /* Light Green */
        padding: 25px;
        border-radius: 20px;
        border: 3px solid #4caf50; /* Strong Green Border */
        box-shadow: 0 4px 12px rgba(76,175,80,0.2);
    }

    /* Styling for all Text Inputs to Glow on Focus */
    .stTextInput input {
        border: 2px solid #b0bec5;
        border-radius: 12px;
        padding: 12px;
        transition: all 0.3s;
    }
    .stTextInput input:focus {
        border-color: #FFD700; /* Yellow highlight */
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
    }
    
    /* Styling for Manager Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f3f4;
        border-radius: 10px 10px 0 0;
        border: 1px solid #dadee0;
        color: #5f6368;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2196f3 !important; /* Active tab blue */
        color: white !important;
    }

    /* General Button Styling (Blue Gradient base) */
    div.stButton > button {
        background: linear-gradient(to right, #2196f3, #1976d2);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 14px 28px;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(33,150,243,0.4);
    }

    /* Reset Button Class (Green Gradient) */
    .reset-btn button {
        background: linear-gradient(to right, #4caf50, #388e3c) !important;
        box-shadow: 0 6px 12px rgba(76,175,80,0.4);
    }
    
    /* Delete Button Class (Red Gradient) */
    .delete-btn button {
        background: linear-gradient(to right, #f44336, #d32f2f) !important;
        box-shadow: 0 6px 12px rgba(244,67,54,0.4);
    }

    /* Custom Colorful Divider */
    hr { border-top: 3px solid #FFD700; margin: 30px 0; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADER ---
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# --- 4. COLORFUL LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.markdown('<div class="school-header"><h1 style="margin:0;">🚌 AKSHARA PUBLIC SCHOOL</h1><p style="margin:0;font-weight:600;">Fleet Management Portal</p></div>', unsafe_allow_html=True)
    
    # Wrap login form in a colorful container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#1565c0;'>🔐 Secure Login</h2>", unsafe_allow_html=True)
    user_input = st.text_input("👤 Enter Username", placeholder="e.g., DRIVER or MANAGER").upper().strip()
    
    if user_input == "MANAGER":
        password = st.text_input("🔑 Manager Password", type="password")
        if st.button("🚀 Login as Manager"):
            if password == "Akshara@2026": 
                st.session_state.role = "manager"; st.session_state.logged_in = True; st.rerun()
            else:
                st.error("❌ Invalid Password")
    else:
        st.write("") # Spacer
        if st.button("🚚 Login as Driver"):
            if not df.empty and user_input in df['driver'].str.upper().str.strip().values:
                st.session_state.role = "driver"; st.session_state.user = user_input; st.session_state.logged_in = True; st.rerun()
            else:
                st.warning("⚠️ Driver not found. Please check username.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. MANAGER DASHBOARD ---
if st.session_state.role == "manager":
    st.markdown('<div class="school-header"><h2 style="margin:0;">🏆 Manager Dashboard</h2></div>', unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📊 Fleet Performance", "➕ Enroll Vehicle", "⚙️ Manage Fleet"])
    
    with t1:
        st.subheader("🏎️ Live Fleet Status")
        if not df.empty:
            m_df = df.copy()
            m_df['Trip KM'] = m_df['odo'] - m_df['trip_km']
            m_df['Mileage'] = m_df.apply(lambda x: round(x['Trip KM'] / x['fuel_liters'], 2) if x['fuel_liters'] > 0 else 0, axis=1)
            
            # Enhanced color styling for mileage
            def style_mileage(v):
                if v > 12: return 'color: #2e7d32; font-weight: 800; background-color: #c8e6c9' # Dark Green on light green
                if v < 8: return 'color: #c62828; font-weight: 800; background-color: #ffcdd2' # Dark Red on light red
                return 'color: #f57f17; font-weight: 600;' # Orange for average

            st.dataframe(m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']].style.applymap(style_mileage, subset=['Mileage']), 
                         use_container_width=True, hide_index=True)
            
            st.write("")
            csv = m_df[['plate', 'driver', 'odo', 'Trip KM', 'Mileage']].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Colorful Report", data=csv, file_name="Akshara_Fleet_Live.csv", mime="text/csv")

    with t2:
        st.subheader("📝 Add New Vehicle")
        col1, col2 = st.columns(2)
        with col1: p_n = st.text_input("🔢 Plate No").upper().strip()
        with col2: d_n = st.text_input("🧑‍✈️ Driver Name").upper().strip()
        st.write("")
        if st.button("💾 Save to Fleet"):
            supabase.table("vehicles").upsert({"plate": p_n, "driver": d_n, "odo": 0, "trip_km": 0, "fuel_liters": 0.0}).execute()
            st.success("✅ Vehicle Added Successfully!")
            st.rerun()

    with t3:
        st.subheader("🗑️ Remove Vehicle")
        if not df.empty:
            target = st.selectbox("Select Vehicle to Remove", df['plate'].unique())
            st.write("")
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if st.button(f"⚠️ Delete {target} Permanently"):
                supabase.table("vehicles").delete().eq("plate", target).execute()
                st.error(f"Vehicle {target} deleted.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 6. COLORFUL DRIVER INTERFACE ---
else:
    st.markdown(f'<div class="school-header"><h2 style="margin:0;">👋 Welcome, {st.session_state.user}</h2></div>', unsafe_allow_html=True)
    
    # Wrap driver content in a green container
    st.markdown('<div class="driver-container">', unsafe_allow_html=True)
    
    v_data = df[df['driver'].str.upper().str.strip() == st.session_state.user].iloc[0]
    trip_dist = v_data['odo'] - v_data['trip_km']
    trip_mileage = round(trip_dist / v_data['fuel_liters'], 2) if v_data['fuel_liters'] > 0 else 0
    
    # Colorful Metric Cards
    c1, c2 = st.columns(2)
    c1.metric("📌 Trip Distance", f"{trip_dist} km")
    c2.metric("⛽ Last Mileage", f"{trip_mileage} km/l")
    
    st.divider()

    # SECTION 1: Blue Header & Button
    st.markdown("<h3 style='color:#1565c0;'>💙 1. Daily Odometer Update</h3>", unsafe_allow_html=True)
    new_odo = st.number_input("Current Meter Reading", min_value=float(v_data['odo']), value=float(v_data['odo']))
    st.write("")
    if st.button("🔄 Update Odometer"):
        supabase.table("vehicles").update({"odo": int(new_odo)}).eq("plate", v_data['plate']).execute()
        st.balloons() # Add balloons for fun!
        st.success("✅ Odometer updated successfully!")
        st.rerun()

    st.divider()

    # SECTION 2: Green Header & Button
    st.markdown("<h3 style='color:#2e7d32;'>💚 2. Fuel Fill-up (Reset)</h3>", unsafe_allow_html=True)
    diesel = st.number_input("Diesel Liters Added", min_value=0.0, value=0.0)
    st.write("")
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("⛽ Log Fuel & Start New Trip"):
        if diesel > 0:
            supabase.table("vehicles").update({"trip_km": int(v_data['odo']), "fuel_liters": float(diesel)}).eq("plate", v_data['plate']).execute()
            st.snow() # Add snow for a cool reset effect!
            st.success("✅ Trip reset! Drive safely.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # End driver-container

st.write("")
if st.sidebar.button("👋 Logout"):
    st.session_state.clear(); st.rerun()
