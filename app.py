# Import necessary libraries
import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt

# Import NSE companies by sector from the external file
from nse_companies import nse_companies_by_sector

# Set up default date range
end_date_default = datetime.now()
start_date_default = end_date_default - timedelta(days=90)  # Roughly three months

# Sidebar components for user inputs
st.sidebar.header("Stock Selection and Date Range")

# Range input
range_number = st.sidebar.number_input("Range:", min_value=1, max_value=365, value=3, step=1)
range_type = st.sidebar.selectbox("Range Type:", ["day", "week", "month", "year"], index=2)

# Calculate the start and end dates based on range type and number
if range_type == "day":
    start_date_default = end_date_default - timedelta(days=range_number)
elif range_type == "week":
    start_date_default = end_date_default - timedelta(weeks=range_number)
elif range_type == "month":
    start_date_default = end_date_default - timedelta(days=30 * range_number)
elif range_type == "year":
    start_date_default = end_date_default - timedelta(days=365 * range_number)

# Date pickers
start_date = st.sidebar.date_input("Start Date:", value=start_date_default)
end_date = st.sidebar.date_input("End Date:", value=end_date_default)

# Sector filter
sector_filter = st.sidebar.selectbox("Select Sector:", ["All"] + list(nse_companies_by_sector.keys()))

# Search box
search_term = st.sidebar.text_input("Search for a company...", "")

# Multi-select for companies
filtered_companies = []
all_companies = []

# Combine all companies into a single list for "All Companies" option
for sector, companies in nse_companies_by_sector.items():
    all_companies.extend(list(companies.keys()))

if sector_filter == "All":
    filtered_companies = all_companies
else:
    filtered_companies = list(nse_companies_by_sector[sector_filter].keys())

if search_term:
    filtered_companies = [company for company in all_companies if search_term.lower() in company.lower()]

selected_companies = st.sidebar.multiselect("Select Companies:", filtered_companies)

# EDA options in the sidebar
eda_options = st.sidebar.multiselect(
    "Select EDA Components:",
    ["Summary Statistics", "Percentage Change Histogram", "Closing Prices Over Time", "Pair Plot", "Heat Map"],
    default=["Summary Statistics", "Percentage Change Histogram", "Closing Prices Over Time"]
)

# Main content: Display selected stocks and fetch data
st.title("NSE Stock Data Viewer")

# Initialize session state for storing data
if "stock_data" not in st.session_state:
    st.session_state.stock_data = pd.DataFrame()

# Fetch data and store it
if st.button("Submit Selection"):
    if not selected_companies:
        st.warning("No stocks selected!")
    elif not start_date or not end_date:
        st.warning("Please select a valid date range!")
    else:
        st.info("Fetching stock data, please wait...")
        all_stock_data = []
        for company in selected_companies:
            for sector, companies in nse_companies_by_sector.items():
                if company in companies:
                    stock_symbol = companies[company]
                    stock = yf.Ticker(stock_symbol)
                    data = stock.history(start=start_date, end=end_date)
                    if not data.empty:
                        for date, row in data.iterrows():
                            percentage_change = ((row["Close"] - row["Open"]) / row["Open"]) * 100
                            all_stock_data.append({
                                "Company": company,
                                "Symbol": stock_symbol,
                                "Date": date.date(),
                                "Open": row["Open"],
                                "High": row["High"],
                                "Low": row["Low"],
                                "Close": row["Close"],
                                "Volume": row["Volume"],
                                "Percentage Change": percentage_change
                            })
                        st.success(f"Fetched data for {company} ({stock_symbol})")
                    else:
                        st.warning(f"No data available for {company} ({stock_symbol})")
        
        if all_stock_data:
            # Store data in session_state
            st.session_state.stock_data = pd.DataFrame(all_stock_data)
            st.success("Data stored successfully for analysis!")
        else:
            st.warning("No data fetched for the selected stocks.")

# EDA Section
if not st.session_state.stock_data.empty:
    st.subheader("Exploratory Data Analysis (EDA)")

    # Display the stored data
    if "Summary Statistics" in eda_options:
        st.write("Stored Stock Data:", st.session_state.stock_data)
        st.write("Summary Statistics:")
        st.write(st.session_state.stock_data.describe())

    if "Percentage Change Histogram" in eda_options:
        st.write("Percentage Change Histogram:")
        st.bar_chart(st.session_state.stock_data["Percentage Change"])

    if "Closing Prices Over Time" in eda_options:
        st.write("Closing Prices Over Time:")
        closing_prices = st.session_state.stock_data.pivot(index="Date", columns="Company", values="Close")
        st.line_chart(closing_prices)

    if "Pair Plot" in eda_options:
        st.write("Pair Plot (Numerical Features):")
        # Plotting the pair plot
        numerical_data = st.session_state.stock_data[["Open", "High", "Low", "Close", "Volume", "Percentage Change"]]
        sns.set(style="whitegrid")
        pair_plot = sns.pairplot(numerical_data, diag_kind="kde")
        st.pyplot(pair_plot.fig)

    if "Heat Map" in eda_options:
        st.write("Heat Map (Correlation Matrix):")
        # Plotting the heat map
        correlation_matrix = st.session_state.stock_data[["Open", "High", "Low", "Close", "Volume", "Percentage Change"]].corr()
        plt.figure(figsize=(10, 8))
        heat_map = sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
        st.pyplot(plt.gcf())
