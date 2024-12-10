import streamlit as st
import pandas as pd
import numpy as np
from garch_helpers import garch_forecast

st.set_page_config(page_title="GARCH Individual Analysis", layout="wide")

st.title("GARCH Individual Asset Analysis")
st.write("Analyze GARCH(1,1) volatility forecasts for individual stocks or assets.")

asset_symbol = st.text_input("Enter the asset symbol (e.g., 'SPY', 'AAPL', 'BTC-USD'):", value="SPY")
if st.button("Run Analysis"):
    try:
        # Call the garch_forecast function
        result = garch_forecast(asset_symbol)

        # Display the analysis details
        st.subheader(f"Analysis for {asset_symbol}")
        st.write(f"**Current Price:** ${result['price']:.2f}")
        st.write(f"**Volatility (1-day forecast):** {result['volatility']:.2f}%")
        st.write(f"**Probability of Success (Direction Based on SMAs):** {result['probability_success']:.2f}%")
        st.write(f"**Directional Bias:** {result['bias']}")
        st.write(f"**Expected 1-day Price Range:** ${result['range'][0]:.2f} - ${result['range'][1]:.2f}")
        st.write(f"**Signal Strength:** {result['signal_strength']:.2f}")

        # Process data for the chart
        data = result['data']

        # Debug: Display data structure
        st.write("Data preview:")
        st.write(data.head())

        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [' '.join(col).strip() for col in data.columns]

        # Ensure the Adj Close column exists
        adj_close_column = None
        for col in data.columns:
            if 'Adj Close' in col or 'Close' in col:
                adj_close_column = col
                break

        if adj_close_column is None:
            raise ValueError("The data does not contain an 'Adj Close' or equivalent column.")

        # Use the identified column for SMA calculations
        data['Adj Close'] = data[adj_close_column]

        # Calculate SMAs explicitly
        data['SMA_20'] = data['Adj Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Adj Close'].rolling(window=50).mean()

        # Drop rows with NaN values (e.g., at the start of the SMA calculation)
        data = data.dropna()

        # Create an interactive Streamlit line chart
        st.line_chart(data[['Adj Close', 'SMA_20', 'SMA_50']])

        # Create a statistical dashboard
        st.subheader("Statistical Dashboard")
        st.write("### Descriptive Statistics")
        st.write(data['Adj Close'].describe())

        st.write("### Rolling Volatility (30-Day)")
        data['Volatility_30'] = data['Adj Close'].pct_change().rolling(window=30).std() * np.sqrt(252)  # Annualized volatility
        st.line_chart(data['Volatility_30'].dropna())

        st.write("### Price Range Analysis")
        st.write(f"Highest Price: ${data['Adj Close'].max():.2f}")
        st.write(f"Lowest Price: ${data['Adj Close'].min():.2f}")

        st.write("### Correlation Analysis")
        correlation = data[['Adj Close', 'SMA_20', 'SMA_50']].corr()
        st.write(correlation)

    except Exception as e:
        # Handle any errors gracefully
        st.error(f"An error occurred: {e}")

st.write("---")
st.write("by Muhammad Usman Abbas")
st.write("""
**Disclaimer**  
This application is for **informational and educational purposes only**.  
It is **Not Financial Advice (NFA)**.  
Please **Do Your Own Research (DYOR)** before making any financial decisions.  
The app is intended for **testing purposes only** and should not be used as the basis for investment or trading decisions.  
**Use at your own risk.**
""")

