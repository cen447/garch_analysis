import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Set up Streamlit page
st.set_page_config(page_title="Stock Trend Analyzer with Predictions", layout="wide")

# Add a logo/image to the sidebar with specified width
st.sidebar.image("growth-chart-invest.png", width=65)

# Title
st.title("Stock Trend Analyzer with Price Prediction")
st.subheader("How Price Prediction Works")
with st.expander("prediction methodology"):
    st.write("""
    **Prediction Methodology:**

    1. **Baseline Growth:**
       - The average daily percentage change in stock prices is used to calculate expected growth over the selected prediction horizon.
       - Formula: 
         \\[
         \\text{Baseline Growth} = (1 + \\text{Average Daily Change})^{\\text{Prediction Horizon}} - 1
         \\]

    2. **Trends:**
       - Short-, medium-, and long-term trends are derived from moving averages:
         - **Short-Term Trend:** Comparison of the 20-day moving average with the current close price.
         - **Medium-Term Trend:** Comparison of the 50-day moving average with the current close price.
         - **Long-Term Trend:** Comparison of the 200-day moving average with the current close price.

       - Formula: 
         \\[
         \\text{Trend} = \\frac{\\text{Moving Average} - \\text{Current Close Price}}{\\text{Current Close Price}}
         \\]

    3. **Weighted Prediction Change:**
       - The trends are weighted (40% each for short- and medium-term trends, 20% for long-term trend) and combined with baseline growth:
         \\[
         \\text{Prediction Change} = (0.4 \\times \\text{Short-Term Trend}) + (0.4 \\times \\text{Medium-Term Trend}) + (0.2 \\times \\text{Long-Term Trend}) + \\text{Baseline Growth}
         \\]

    4. **Predicted Price:**
       - The predicted price is calculated as:
         \\[
         \\text{Predicted Price} = \\text{Current Close Price} \\times (1 + \\text{Prediction Change})
         \\]

    5. **Confidence Interval:**
       - A range of potential prices is calculated using historical volatility:
         \\[
         \\text{Confidence Interval} = \\left( \\text{Predicted Price} \\times (1 - \\text{Volatility}), \\text{Predicted Price} \\times (1 + \\text{Volatility}) \\right)
         \\]
       - Volatility is the standard deviation of daily percentage changes.

    **Key Notes:**
    - The model relies on historical trends and does not account for unforeseen market events.
    - Confidence intervals provide a range where the price is likely to fall, not a guarantee.
    """)

st.write("""
Analyze stock trends with multiple technical indicators, predict short-term price movements, and stay updated with news and fundamental reports.
""")

# Input for stock symbol
symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA):", value="AAPL")

# Default values for short-, medium-, and long-term moving averages
short_term = 20
medium_term = 50
long_term = 200

if symbol:
    stock = yf.Ticker(symbol)
    try:
        # Fetch historical data
        df = stock.history(period="1y")
        if df.empty:
            st.error(f"No historical data available for {symbol}. Please try a different symbol.")
        else:
            # Calculate Moving Averages
            df['Short_MA'] = df['Close'].rolling(window=short_term).mean()
            df['Medium_MA'] = df['Close'].rolling(window=medium_term).mean()
            df['Long_MA'] = df['Close'].rolling(window=long_term).mean()

            # Calculate RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Calculate Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            df['BB_Upper'] = df['BB_Middle'] + 2 * df['Close'].rolling(window=20).std()
            df['BB_Lower'] = df['BB_Middle'] - 2 * df['Close'].rolling(window=20).std()

            # Plot stock price with Moving Averages
            fig_price = go.Figure()
            fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['Short_MA'], mode='lines', name=f'{short_term}-Day MA'))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['Medium_MA'], mode='lines', name=f'{medium_term}-Day MA'))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['Long_MA'], mode='lines', name=f'{long_term}-Day MA'))
            fig_price.update_layout(title="Stock Price and Moving Averages", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig_price, use_container_width=True)

            # Bollinger Bands Chart
            fig_bb = go.Figure()
            fig_bb.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
            fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], mode='lines', name='Upper Band'))
            fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], mode='lines', name='Lower Band'))
            fig_bb.update_layout(title="Bollinger Bands", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig_bb, use_container_width=True)

            # RSI Chart
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI'))
            fig_rsi.update_layout(title="Relative Strength Index (RSI)", xaxis_title="Date", yaxis_title="RSI")
            fig_rsi.add_shape(type="line", x0=df.index[0], x1=df.index[-1], y0=70, y1=70, line=dict(color="red", dash="dot"))
            fig_rsi.add_shape(type="line", x0=df.index[0], x1=df.index[-1], y0=30, y1=30, line=dict(color="green", dash="dot"))
            st.plotly_chart(fig_rsi, use_container_width=True)

            # Prediction Slider
            st.header("Prediction Slider")
            prediction_horizon = st.slider("Select Prediction Horizon (Days):", min_value=1, max_value=30, value=5)

            # Calculate Historical Baseline
            df['Pct_Change'] = df['Close'].pct_change()
            avg_daily_change = df['Pct_Change'].mean()
            baseline_growth = (1 + avg_daily_change) ** prediction_horizon - 1

            # Calculate Trends
            short_trend = (df['Short_MA'].iloc[-1] - df['Close'].iloc[-1]) / df['Close'].iloc[-1]
            medium_trend = (df['Medium_MA'].iloc[-1] - df['Close'].iloc[-1]) / df['Close'].iloc[-1]
            long_trend = (df['Long_MA'].iloc[-1] - df['Close'].iloc[-1]) / df['Close'].iloc[-1]

            # Weighted Prediction
            prediction_change = (
                0.4 * short_trend + 0.4 * medium_trend + 0.2 * long_trend
            ) + baseline_growth

            predicted_price = df['Close'].iloc[-1] * (1 + prediction_change)
            percentage_change = prediction_change * 100

            # Confidence Interval
            historical_volatility = df['Pct_Change'].std() * np.sqrt(prediction_horizon)
            confidence_interval = (
                predicted_price * (1 - historical_volatility),
                predicted_price * (1 + historical_volatility),
            )

            # Prediction Details
            st.header("Prediction Details")
            st.write(f"**Current Price:** ${df['Close'].iloc[-1]:.2f}")
            st.write(f"**Predicted Price in {prediction_horizon} Days:** ${predicted_price:.2f}")
            st.write(f"**Price Change:** ${predicted_price - df['Close'].iloc[-1]:.2f}")
            st.write(f"**Percentage Change:** {percentage_change:.2f}%")
            st.write(f"**Confidence Interval:** (${confidence_interval[0]:.2f}, ${confidence_interval[1]:.2f})")

            # Confidence Interval Explanation
            st.subheader("How to Interpret the Confidence Interval")
            st.write("""
            - The confidence interval represents the range where the predicted price is likely to fall.
            - Narrow intervals suggest more certainty; wide intervals suggest higher market volatility.
            """)

            # Latest News
            st.header("Latest News")
            try:
                news_data = stock.news
                if news_data:
                    for item in news_data[:5]:
                        st.write(f"**{item.get('title', 'No Title')}**")
                        summary = item.get('summary', 'No summary available.')
                        st.write(f"{summary}")
                        st.write(f"[Read more]({item.get('link', '#')})")
                        st.write("---")
                else:
                    st.write("No news available for this stock.")
            except Exception as e:
                st.error(f"An error occurred while fetching news: {e}")

            # Fundamental Analysis
            st.header("Fundamental Analysis")

            try:
                # Fetch stock information
                info = stock.info

                # Extract fundamental metrics
                valuation_ratios = {
                    "P/E Ratio (Trailing)": info.get("trailingPE", "N/A"),
                    "P/E Ratio (Forward)": info.get("forwardPE", "N/A"),
                    "Price-to-Book (P/B)": info.get("priceToBook", "N/A"),
                    "Price-to-Sales (P/S)": info.get("priceToSalesTrailing12Months", "N/A"),
                    "EV/Revenue": info.get("enterpriseToRevenue", "N/A"),
                    "EV/EBITDA": info.get("enterpriseToEbitda", "N/A"),
                }

                profitability_ratios = {
                    "Profit Margins": f"{info.get('profitMargins', 'N/A'):.2%}" if info.get('profitMargins') else "N/A",
                    "Return on Assets (ROA)": f"{info.get('returnOnAssets', 'N/A'):.2%}" if info.get('returnOnAssets') else "N/A",
                    "Return on Equity (ROE)": f"{info.get('returnOnEquity', 'N/A'):.2%}" if info.get('returnOnEquity') else "N/A",
                    "Operating Margins": f"{info.get('operatingMargins', 'N/A'):.2%}" if info.get('operatingMargins') else "N/A",
                    "Gross Margins": f"{info.get('grossMargins', 'N/A'):.2%}" if info.get('grossMargins') else "N/A",
                }

                liquidity_metrics = {
                    "Current Ratio": info.get("currentRatio", "N/A"),
                    "Quick Ratio": info.get("quickRatio", "N/A"),
                }

                debt_metrics = {
                    "Debt-to-Equity": info.get("debtToEquity", "N/A"),
                    "Total Debt": f"${info.get('totalDebt', 'N/A'):,}" if info.get("totalDebt") else "N/A",
                }

                growth_metrics = {
                    "Earnings Growth": f"{info.get('earningsGrowth', 'N/A'):.2%}" if info.get('earningsGrowth') else "N/A",
                    "Revenue Growth": f"{info.get('revenueGrowth', 'N/A'):.2%}" if info.get('revenueGrowth') else "N/A",
                }

                # Combine all metrics for visualization
                metrics_df = pd.DataFrame({
                    "Category": [
                        "Valuation Ratios", "Valuation Ratios", "Valuation Ratios", "Valuation Ratios",
                        "Valuation Ratios", "Valuation Ratios",
                        "Profitability Ratios", "Profitability Ratios", "Profitability Ratios",
                        "Profitability Ratios", "Profitability Ratios",
                        "Liquidity Metrics", "Liquidity Metrics",
                        "Debt Metrics", "Debt Metrics",
                        "Growth Metrics", "Growth Metrics"
                    ],
                    "Metric": list(valuation_ratios.keys()) + list(profitability_ratios.keys()) + list(liquidity_metrics.keys()) + list(debt_metrics.keys()) + list(growth_metrics.keys()),
                    "Value": list(valuation_ratios.values()) + list(profitability_ratios.values()) + list(liquidity_metrics.values()) + list(debt_metrics.values()) + list(growth_metrics.values())
                })

                # Display as table
                st.subheader("Metrics Table")
                st.dataframe(metrics_df)

                # Visualize as bar chart
                st.subheader("Metrics Visualization")
                fig_metrics = px.bar(metrics_df, x="Metric", y="Value", color="Category",
                                     title="Fundamental Metrics", labels={"Value": "Metric Value"}, height=600)
                st.plotly_chart(fig_metrics, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to fetch fundamental data: {e}")

    except Exception as e:
        st.error(f"An error occurred while processing data for {symbol}: {e}")
