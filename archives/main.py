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

        # Handle missing or renamed columns
        adj_close_column = None
        for col in data.columns:
            if 'Adj Close' in col or 'Close' in col:
                adj_close_column = col
                break

        if adj_close_column is None:
            raise ValueError("The data does not contain an 'Adj Close' or equivalent column.")

        # Rename the identified column for consistency
        data = data.rename(columns={adj_close_column: 'Adj Close'})

        # Add SMAs
        data['SMA_20'] = data['Adj Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Adj Close'].rolling(window=50).mean()

        # Drop rows with NaN values for clean chart rendering
        chart_data = data[['Adj Close', 'SMA_20', 'SMA_50']].dropna()

        # Create an interactive Streamlit line chart
        st.line_chart(chart_data)

    except Exception as e:
        # Handle any errors gracefully
        st.error(f"An error occurred: {e}")

st.write("---")
st.write("by Muhammad Usman Abbas")
