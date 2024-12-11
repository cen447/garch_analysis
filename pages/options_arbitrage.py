import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Options Arbitrage Scanner", layout="wide")

# Add a logo/image to the sidebar with specified width
st.sidebar.image("growth-chart-invest.png", width=65)

st.title("Options Arbitrage Scanner")
st.write("""
This app analyzes options arbitrage opportunities based on **put-call parity** and helps identify the best contracts to buy and sell to exploit mispricing in the market.

---

### What is Put-Call Parity?
Put-call parity ensures the relationship between the prices of call options, put options, and the underlying asset remains balanced in an efficient market. Deviations from this relationship create arbitrage opportunities.

The formula is:
\[
C - P = S - K \cdot e^{-rT}
\]
Where:
- \( C \): Call option price
- \( P \): Put option price
- \( S \): Current price of the underlying asset.
- \( K \): Strike price.
- \( r \): Risk-free interest rate (as a decimal, e.g., 4.20% = 0.042).
- \( T \): Time to maturity (in years).

---

### How Do You Make Money?
1. **Positive Parity Difference (\( C - P > S - K \cdot e^{-rT} \)):**
   - **Action:** Sell the call, buy the put, and buy the underlying stock.
   - **Profit:** Lock in the difference between theoretical and market prices after fees.

2. **Negative Parity Difference (\( C - P < S - K \cdot e^{-rT} \)):**
   - **Action:** Buy the call, sell the put, and short the underlying stock.
   - **Profit:** Reverse the mispricing trade to earn the difference.

---
""")

with st.expander("Click here to understand the strategy and how profits are made"):
    st.write("""
    ### Explanation: Why You Hold the Stock Long or Short in Arbitrage Trading
    In options arbitrage strategies based on **put-call parity**, the stock position (long or short) balances the arbitrage trade and ensures you lock in the profit without market risk.

    ### How Put-Call Parity Works
    The fundamental relationship:
    \[
    C - P = S - K \cdot e^{-rT}
    \]
    Where:
    - \( C \): Call option price.
    - \( P \): Put option price.
    - \( S \): Current price of the underlying stock.
    - \( K \): Strike price of the options.
    - \( r \): Risk-free interest rate.
    - \( T \): Time to maturity (in years).

    ---
    ### Case 1: Positive Parity Opportunity
    **When \( C - P > S - K \cdot e^{-rT} \):**
    - **What You Do**:
      1. Sell the call.
      2. Buy the put.
      3. Buy the stock.
    - **Why Hold the Stock (Long)**:
      - If the call is exercised, you need to deliver the stock. By owning it, you eliminate the risk of having to buy it at a higher price.
      - The put protects you if the stock price falls.
    - **Profit**:
      - Comes from the mispricing between the call, put, and stock prices.
      - Example:
        - Stock Price (\( S \)): $100.
        - Call Price (\( C \)): $8.
        - Put Price (\( P \)): $3.
        - Strike Price (\( K \)): $105.
      - Actions:
        - Sell Call (\( +8 \)).
        - Buy Put (\( -3 \)).
        - Buy Stock (\( -100 \)).
      - Profit at Expiration (\( S \leq K \)): \( K - Total Cost \).
        - If \( S = 105 \): \( 105 - 95 = 10 \).

    ---
    ### Case 2: Negative Parity Opportunity
    **When \( C - P < S - K \cdot e^{-rT} \):**
    - **What You Do**:
      1. Buy the call.
      2. Sell the put.
      3. Short the stock.
    - **Why Short the Stock**:
      - If the put is exercised, you must buy the stock at the strike price. Shorting ensures you can lock in the current market price.
      - The call protects you if the stock price rises.
    - **Profit**:
      - Comes from the mispricing between the call, put, and stock prices.
      - Example:
        - Stock Price (\( S \)): $100.
        - Call Price (\( C \)): $2.
        - Put Price (\( P \)): $6.
        - Strike Price (\( K \)): $95.
      - Actions:
        - Buy Call (\( -2 \)).
        - Sell Put (\( +6 \)).
        - Short Stock (\( +100 \)).
      - Profit at Expiration (\( S \geq K \)): \( Short Sale Proceeds - Cost to Repurchase \).
        - If \( S = 95 \): \( 100 - 95 - 2 + 6 = 9 \).

    ---
    ### Why You Hold or Short the Stock
    The stock position ensures that:
    1. **Hedging Risk**: Protects you from price movements.
    2. **Meeting Obligations**: Covers any exercise of the call or put.
    3. **Guaranteed Profit**: Locks in the difference caused by mispricing.

    **Holding Period**: You hold the stock or short position until the options expiration date, at which point the trade resolves, and you collect the profit.
    """)

# Input for stock symbol
symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA, SPY):", value="AAPL")

# Input for risk-free rate with default value of 4.20%
risk_free_rate = st.number_input(
    "Enter the risk-free rate (%):",
    min_value=0.0,
    value=4.20,
) / 100  # Convert percentage to decimal

# Slider for time frame (in days)
time_frame = st.slider("Select time frame for expiration dates (in days):", min_value=0, max_value=365, value=(0, 60))

# Input for trading fees
trading_fee = st.number_input(
    "Enter trading fee per contract ($):",
    min_value=0.0,
    value=1.0,  # Assume $1 fee by default
)

# Button to process arbitrage calculation
if st.button("Process Arbitrage Opportunities"):
    with st.spinner("Analyzing arbitrage opportunities..."):
        try:
            # Fetch option chain data
            stock = yf.Ticker(symbol)
            options_expirations = stock.options
            if not options_expirations:
                st.error("No options data available for this stock.")
                st.stop()

            # Filter expiration dates within the selected time frame
            today = datetime.now()
            filtered_expirations = [
                exp for exp in options_expirations
                if 0 <= (datetime.strptime(exp, '%Y-%m-%d') - today).days <= time_frame[1]
            ]

            if not filtered_expirations:
                st.error("No expiration dates found within the selected time frame.")
                st.stop()

            st.write(f"Scanning arbitrage opportunities for {symbol} within {time_frame[0]} to {time_frame[1]} days:")

            results = []

            for expiration in filtered_expirations:
                expiration_date = datetime.strptime(expiration, '%Y-%m-%d')
                time_to_maturity = (expiration_date - today).days / 365  # Time to maturity in years
                options = stock.option_chain(expiration)

                # Get calls and puts
                calls = options.calls
                puts = options.puts

                # Merge calls and puts on strike price
                merged = pd.merge(
                    calls[['strike', 'lastPrice']],
                    puts[['strike', 'lastPrice']],
                    on='strike',
                    suffixes=('_call', '_put')
                )

                # Calculate put-call parity
                underlying_price = stock.history(period="1d")['Close'][-1]
                merged['parity_diff'] = (merged['lastPrice_call'] - merged['lastPrice_put']) - \
                    (underlying_price - merged['strike'] * np.exp(-risk_free_rate * time_to_maturity))

                # Add expiration date for context
                merged['expiration'] = expiration

                # Separate positive and negative parity
                positive_parity = merged[merged['parity_diff'] > 0]
                negative_parity = merged[merged['parity_diff'] < 0]

                # Filter for opportunities with positive profits
                positive_parity['profit'] = (positive_parity['parity_diff'] - trading_fee) * 100
                negative_parity['profit'] = (-negative_parity['parity_diff'] - trading_fee) * 100

                positive_parity = positive_parity[positive_parity['profit'] > 0]
                negative_parity = negative_parity[negative_parity['profit'] > 0]

                # Skip this expiration if no profitable opportunities
                if positive_parity.empty and negative_parity.empty:
                    continue

                # Find the best positive and negative opportunities
                best_positive = (
                    positive_parity.loc[positive_parity['profit'].idxmax()] if not positive_parity.empty else None
                )
                best_negative = (
                    negative_parity.loc[negative_parity['profit'].idxmax()] if not negative_parity.empty else None
                )

                results.append((expiration, best_positive, best_negative, underlying_price, expiration_date, merged))

            # Display results with collapsible sections
            if results:
                for exp, best_positive, best_negative, underlying_price, expiration_date, merged in results:
                    with st.expander(f"Expiration Date: {exp}"):
                        st.write("#### Full Opportunity Table:")
                        st.dataframe(merged)

                        holding_period = (expiration_date - today).days
                        st.write(f"### Holding Period: {holding_period} days")

                        if best_positive is not None:
                            st.write("#### Best Positive Parity Opportunity:")
                            total_cost = best_positive['lastPrice_put'] * 100 + underlying_price * 100
                            st.write(f"- **Call Premium Earned (Sell Call):** ${best_positive['lastPrice_call'] * 100:.2f}")
                            st.write(f"- **Put Premium Paid (Buy Put):** ${best_positive['lastPrice_put'] * 100:.2f}")
                            st.write(f"- **Stock Purchase Cost:** ${underlying_price * 100:.2f}")
                            st.write(f"- **Total Investment Required:** ${total_cost:.2f}")
                            st.write(f"- **Profit After Fees:** ${best_positive['profit']:.2f}")
                            st.write(f"- **Profit Percentage:** {best_positive['profit'] / total_cost * 100:.2f}%")
                            st.write("---")

                        if best_negative is not None:
                            st.write("#### Best Negative Parity Opportunity:")
                            total_cost = best_negative['lastPrice_call'] * 100
                            st.write(f"- **Call Premium Paid (Buy Call):** ${best_negative['lastPrice_call'] * 100:.2f}")
                            st.write(f"- **Put Premium Earned (Sell Put):** ${best_negative['lastPrice_put'] * 100:.2f}")
                            st.write(f"- **Short Stock Cost:** ${underlying_price * 100:.2f}")
                            st.write(f"- **Total Investment Required:** ${total_cost:.2f}")
                            st.write(f"- **Profit After Fees:** ${best_negative['profit']:.2f}")
                            st.write(f"- **Profit Percentage:** {best_negative['profit'] / total_cost * 100:.2f}%")
                            st.write("---")
            else:
                st.write("No profitable arbitrage opportunities detected within the selected time frame.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
