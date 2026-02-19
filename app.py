import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- DATABASE CONNECTION ---
try:
    # This pulls your real keys from the Secrets box you just updated
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("⚠️ DATABASE KEYS ARE STILL PLACEHOLDERS")
    st.info("Please follow Step 2 above to replace the text in Streamlit Secrets.")
    st.stop()

# --- APP START ---
st.set_page_config(page_title="Akshara Vehicle System", layout="wide")
st.markdown("<h1 style='text-align: center;'>AKSHARA PUBLIC SCHOOL</h1>", unsafe_allow_html=True)
st.divider()

# Load data from your new 'vehicles' table
def load_data():
    try:
        res = supabase.table("vehicles").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

df = load_data()

# Login & App Logic...
if st.button("Enroll PRAVEEN"):
    supabase.table("vehicles").insert({"plate": "KA37A8646", "driver": "PRAVEEN", "odo": 0}).execute()
    st.success("Successfully saved to the cloud!")
    st.rerun()
