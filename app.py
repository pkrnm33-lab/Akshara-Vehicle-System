# ==========================================================
# MANAGER: EXPENSE CALCULATOR
# ==========================================================
st.markdown("---")
st.header("💰 Monthly Expense Calculator")

# 1. User Inputs for Calculation
col1, col2 = st.columns(2)
with col1:
    fuel_price = st.number_input("Enter Diesel Price per Liter (₹)", min_value=0.0, value=90.0)
with col2:
    selected_month = st.selectbox("Select Month for Report", ["February", "March", "April"])

# 2. Perform Calculations
if not hist_df.empty:
    # Filter by date (if you have multiple months of data)
    total_liters = hist_df['liters'].sum()
    total_cost = total_liters * fuel_price
    total_km = hist_df['odo'].max() - hist_df['odo'].min() # Simple estimate
    
    # 3. Display Results in Large Cards
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Diesel Consumed", f"{total_liters:.2f} L")
    m2.metric("Total Fuel Expense", f"₹ {total_cost:,.2f}")
    m3.metric("Fleet Avg Mileage", f"{(total_km/total_liters if total_liters > 0 else 0):.2f} KM/L")
    
    # 4. Expense Breakdown Table
    st.subheader("Vehicle-wise Expense Breakdown")
    breakdown = hist_df.groupby('plate').agg({
        'liters': 'sum',
        'mileage': 'mean'
    }).reset_index()
    breakdown['Total Cost (₹)'] = breakdown['liters'] * fuel_price
    st.table(breakdown)
else:
    st.info("No log data available to calculate expenses yet.")
