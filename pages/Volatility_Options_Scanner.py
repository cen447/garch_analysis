import streamlit as st
from garch_helpers import garch_forecast
import pandas as pd
import time

st.set_page_config(page_title="Volatility Options Scanner", layout="wide")

st.title("Volatility Scanner for Options")
st.write("This page analyzes a list of stocks and identifies the most volatile options candidates.")

# Technical explanation of the logic and math in an expander
with st.expander("Technical Details: GARCH Model, SMA Directional Bias, and Probabilities"):
    st.write(r"""
    **1. GARCH(1,1) Model Fundamentals:**

    The GARCH(1,1) model is used to model and forecast time-varying volatility in financial time series. For a return series \( r_t \), 
    we assume:
    \[
    r_t = \mu + \epsilon_t, \quad \epsilon_t = \sigma_t z_t, \quad z_t \sim i.i.d. \ N(0,1)
    \]
    The volatility process \(\sigma_t^2\) follows:
    \[
    \sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2
    \]
    where:
    - \(\omega > 0\) is a long-term average volatility level parameter.
    - \(\alpha \geq 0\) captures the ARCH effect: how past squared shocks \(\epsilon_{t-1}^2\) affect current volatility.
    - \(\beta \geq 0\) captures the GARCH effect: how past volatility \(\sigma_{t-1}^2\) carries over into current volatility.

    After fitting the GARCH model to the historical return data, we use the model's parameters to forecast next-day volatility \(\sigma_{t+1}\). 
    This forecasted standard deviation provides an estimate of the expected price range.

    **2. Directional Bias Using Simple Moving Averages (SMAs):**

    We compute two SMAs:
    - 20-day SMA: \( \text{SMA}_{20} = \frac{1}{20} \sum_{i=0}^{19} P_{t-i} \)
    - 50-day SMA: \( \text{SMA}_{50} = \frac{1}{50} \sum_{i=0}^{49} P_{t-i} \)

    If \(\text{SMA}_{20} > \text{SMA}_{50}\), we interpret the short-term trend as bullish. Conversely, if \(\text{SMA}_{20} < \text{SMA}_{50}\), we consider it bearish. 
    If they're approximately equal, we consider the trend neutral.

    **3. Probability Calculations:**

    Once we have the forecasted volatility \(\sigma\) (in percent form), we can translate it to a price range. For a given current price \(P\), the expected 1-day range is:
    \[
    P_{\text{lower}} = P \times (1 - \sigma/100), \quad P_{\text{upper}} = P \times (1 + \sigma/100).
    \]

    To gauge the probability of a certain directional move, we make a simplifying assumption that daily returns are normally distributed with mean 0 and standard deviation \(\sigma\).

    For a bullish trend, we might test the probability of achieving a +2% move. The 2% threshold in terms of standardized returns is:
    \[
    Z = \frac{0.02}{\sigma/100} = \frac{2\%}{\sigma}
    \]

    The probability of exceeding this threshold under a standard normal assumption is:
    \[
    \Pr(R_t > 2\%) = 1 - \Phi(Z)
    \]

    For a bearish trend, we do a similar calculation for a -2% move:
    \[
    Z = \frac{2\%}{\sigma}, \quad \Pr(R_t < -2\%) = \Phi(-Z).
    \]

    Thus, depending on the trend, we choose an appropriate threshold and compute the probability of exceeding that threshold in the direction of the trend.

    **4. Signal Strength:**

    \[
    \text{signal_strength} = \sigma \times \Pr(\text{success})
    \]

    This simple metric combines the volatility level and the directional probability. A high signal strength suggests both high volatility and a reasonable probability of a trend-aligned move, appealing to options traders seeking large directional moves.

    **5. Outside Range Highlighting:**

    If the current price \(P\) is outside \([P_{\text{lower}}, P_{\text{upper}}]\), we highlight that row to indicate unusual price action.

    In essence, this tool scans a list of stocks, identifies which ones have higher forecasted volatility, computes directional biases and probabilities, and provides a ranked overview to guide options trading decisions.
    """)

# Default stock list
default_stocks = [
    'AAPL', 'TSLA', 'AMD', 'MSFT', 'SPY', 'QQQ', 'NVDA', 'AMZN', 'NIO',
    'SOFI', 'F', 'PLTR', 'LCID', 'CHPT', 'AMC', 'PINS', 'AA', 'SNAP', 'BB',
    'XLF', 'IWM', 'EEM', 'ARKK', 'SLV', 'FXI', 'BABA', 'JD', 'RIOT',
    'MARA', 'T', 'PBR', 'TLT', 'UNG', 'GDX', 'KRE', 'XOP', 'XLE', 'SPXL',
    'SOXS', 'UVXY', 'LABU', 'SQQQ', 'NCLH'
]

# Initialize session state for user-added tickers
if "user_tickers" not in st.session_state:
    st.session_state.user_tickers = []

st.write("**Default asset list:**")
st.write(", ".join(default_stocks))

# Input for adding a single ticker at a time
new_ticker = st.text_input("Add a new ticker (e.g. 'AAPL'):")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Add Ticker"):
        ticker = new_ticker.strip().upper()
        if ticker and ticker not in st.session_state.user_tickers:
            st.session_state.user_tickers.append(ticker)
            st.success(f"Added {ticker}")
        elif ticker in st.session_state.user_tickers:
            st.warning("Ticker already added.")
        else:
            st.warning("Please enter a valid ticker symbol.")

with col2:
    st.write("Current user-added tickers:")
    st.write(", ".join(st.session_state.user_tickers) if st.session_state.user_tickers else "None added yet.")

# Final list of stocks to analyze when user clicks "Run Scan"
full_stock_list = default_stocks.copy()

if st.button("Run Scan"):
    if st.session_state.user_tickers:
        full_stock_list.extend(st.session_state.user_tickers)

    st.write("**Analyzing the following stocks:**")
    st.write(", ".join(full_stock_list))

    st.info("Analyzing your stocks... Grab a cup of coffee while we process your request.")

    total_stocks = len(full_stock_list)
    progress_bar = st.progress(0)  # Initialize progress bar
    
    results = []
    with st.spinner("Working on it..."):
        for i, stock in enumerate(full_stock_list):
            try:
                result = garch_forecast(stock)
                results.append(result)
            except Exception as e:
                st.warning(f"Could not analyze {stock}: {e}")
            # Update progress
            progress_bar.progress((i+1)/total_stocks)
            time.sleep(0.05)  # Slight delay to show progress increment

    if results:
        sorted_results = sorted(results, key=lambda x: x['signal_strength'], reverse=True)

        bullish = [res for res in sorted_results if res['bias'] == 'Bullish']
        bearish = [res for res in sorted_results if res['bias'] == 'Bearish']

        def create_dataframe(results):
            df = pd.DataFrame(results)
            # Convert columns to more user-friendly formats
            df['Current Price'] = df['price'].apply(lambda x: f"${x:.2f}")
            df['Signal Strength'] = df['signal_strength'].apply(lambda x: f"{x:.2f}")
            df['Probability (%)'] = df['probability_success'].apply(lambda x: f"{x:.2f}")
            df['Volatility (%)'] = df['volatility'].apply(lambda x: f"{x:.2f}")
            df['Expected 1-day Range'] = df['range'].apply(lambda r: f"${r[0]:.2f} - ${r[1]:.2f}")

            # Select and order columns for display
            display_cols = [
                'symbol', 'Current Price', 'Signal Strength', 
                'Probability (%)', 'Volatility (%)', 'Expected 1-day Range', 'bias', 'outside_range'
            ]
            df = df[display_cols]
            df.rename(columns={'symbol': 'Symbol', 'bias': 'Bias', 'outside_range': 'Outside Range'}, inplace=True)
            return df

        def highlight_outside_range(row):
            # Highlight rows where Outside Range is True
            if row['Outside Range']:
                return ['background-color: #772b2b'] * len(row)
            return [''] * len(row)

        if bullish:
            st.subheader("Bullish Stocks")
            bullish_df = create_dataframe(bullish)
            st.dataframe(bullish_df.style.apply(highlight_outside_range, axis=1))
        else:
            st.write("No bullish stocks found.")

        if bearish:
            st.subheader("Bearish Stocks")
            bearish_df = create_dataframe(bearish)
            st.dataframe(bearish_df.style.apply(highlight_outside_range, axis=1))
        else:
            st.write("No bearish stocks found.")
    else:
        st.write("No valid results.")

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

