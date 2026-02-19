import streamlit as st
from supabase import create_client
import pandas as pd

# --- INITIALIZE SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Akshara Fleet Tracker", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1E3A8A; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Role", ["📝 Driver Log", "🔐 Manager Login"])

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #4B5563;'>R.G ROAD GANGAVATHI</h4>", unsafe_allow_html=True)
st.markdown("---")

# --- FETCH DATA ---
try:
    response = supabase.table("vehicles").select("*").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Connection Error: {e}")
    df = pd.DataFrame()

# ==========================================================
# PAGE 1: DRIVER LOG
# ==========================================================
if page == "📝 Driver Log":
    st.header("Daily Trip & Fuel Log")
    if not df.empty:
        driver_options = [f"{row['driver']} ({row['plate']})" for _, row in df.iterrows()]
        with st.form("driver_entry", clear_on_submit=True):
            selected_driver = st.selectbox("Identify Yourself", driver_options)
            odo_reading = st.number_input("Current Odometer Reading (KM)", min_value=0)
            fuel_liters = st.number_input("Diesel Added (Liters)", min_value=0.0)
            if st.form_submit_button("Submit Daily Log"):
                driver_name = selected_driver.split(" (")[0]
                row_id = df[df['driver'] == driver_name]['id'].values[0]
                try:
                    supabase.table("vehicles").update({"odo": odo_reading, "fuel_liters": fuel_liters}).eq("id", row_id).execute()
                    st.success("✅ Log submitted successfully!")
                except Exception as e:
                    st.error(f"Error saving log: {e}")
    else:
        st.info("No drivers enrolled. Contact the Manager.")

# ==========================================================
# PAGE 2: MANAGER DASHBOARD (Password Protected)
# ==========================================================
elif page == "🔐 Manager Login":
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.subheader("Administrative Access")
        input_password = st.text_input("Enter Manager Password", type="password")
        if st.button("Login"):
            # The password you requested
            if input_password == "Akshara@2026": 
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password")
    
    else:
        st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))
        st.header("🛠️ Manager Dashboard")
        
        tab1, tab2 = st.tabs(["📊 Fleet History", "➕ Admin Controls"])
        
        with tab1:
            if not df.empty:
                st.dataframe(df[["id", "plate", "driver", "odo", "trip_km", "fuel_liters"]], use_container_width=True, hide_index=True)
            else:
                st.info("No records found.")

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Enroll New Driver")
                with st.form("enroll", clear_on_submit=True):
                    p_no = st.text_input("Plate Number")
                    d_name = st.text_input("Full Name")
                    if st.form_submit_button("Enroll"):
                        try:
                            supabase.table("vehicles").insert({"plate": p_no, "driver": d_name, "odo": 0, "trip_km": 0, "fuel_liters": 0}).execute()
                            st.success(f"Enrolled {d_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Enrollment Error: {e}")
            
            with col2:
                st.subheader("Danger Zone")
                if not df.empty:
                    to_delete = st.selectbox("Select Driver to Delete", df['driver'].tolist())
                    if st.button("🗑️ Delete Permanently"):
                        try:
                            supabase.table("vehicles").delete().eq("driver", to_delete).execute()
                            st.success(f"Deleted {to_delete}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
