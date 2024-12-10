import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from arch import arch_model
from datetime import datetime, timedelta
from scipy.stats import norm

def garch_forecast(asset_symbol, days=2):
    # Step 1: Set the Date Range Dynamically
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    print(f"\nFetching data for {asset_symbol} from {start_date} to {end_date}...")
    data = yf.download(asset_symbol, start=start_date, end=end_date)

    # Calculate Daily Returns (Percentage Change)
    data['Return'] = 100 * data['Adj Close'].pct_change()
    data.dropna(inplace=True)

    # Step 2: Fit the EGARCH Model
    print("Fitting the EGARCH(1,1) model...")
    model = arch_model(data['Return'], vol='EGARCH', p=1, q=1, dist='normal')
    results = model.fit(update_freq=5, disp="off")
    print(results.summary())

    # Step 3: Generate Rolling Forecast for Multi-Day Horizons
    forecast_variance = []
    temp_data = data['Return'].copy()

    for _ in range(days):
        # Fit the model and forecast 1 day ahead at each step
        model = arch_model(temp_data, vol='EGARCH', p=1, q=1, dist='normal')
        results = model.fit(disp="off")
        forecast = results.forecast(horizon=1)
        variance = forecast.variance.values[-1, 0]
        forecast_variance.append(np.sqrt(variance))

        # Add a placeholder observation (simulating next day) using pd.concat()
        temp_data = pd.concat([temp_data, pd.Series([0])], ignore_index=True)

    print(f"\n{days}-day forecasted volatility (std): {forecast_variance[-1]:.2f}%")

    # Step 4: Fetch the Current Price
    ticker = yf.Ticker(asset_symbol)
    current_price = ticker.history(period="1d")['Close'].iloc[-1]

    if isinstance(current_price, pd.Series):
        current_price = current_price.iloc[0]

    print(f"\nCurrent Price: {current_price:.2f}")

    # Calculate Expected Price Range for Each Day
    for i, vol in enumerate(forecast_variance):
        upper = current_price * (1 + vol / 100)
        lower = current_price * (1 - vol / 100)
        print(f"Expected price range for day {i+1}: {lower:.2f} - {upper:.2f}")

    # Step 5: Plot the Data and Indicators
    data['SMA_20'] = data['Adj Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Adj Close'].rolling(window=50).mean()

    plt.figure(figsize=(12, 6))
    plt.plot(data['Adj Close'], label='Adj Close')
    plt.plot(data['SMA_20'], label='20-day SMA', linestyle='--')
    plt.plot(data['SMA_50'], label='50-day SMA', linestyle='--')
    plt.title(f"{asset_symbol} Price with Moving Averages")
    plt.legend()
    plt.show()

# Main loop to analyze multiple stocks
while True:
    asset_symbol = input("\nEnter the asset symbol (e.g., 'SPY', 'BTC-USD') or 'exit' to quit: ").strip()
    if asset_symbol.lower() == 'exit':
        print("Exiting the program. Goodbye!")
        break
    try:
        garch_forecast(asset_symbol, days=2)
    except Exception as e:
        print(f"An error occurred: {e}. Please try again with a valid symbol.")
