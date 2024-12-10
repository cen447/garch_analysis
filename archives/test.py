import yfinance as yf
import pandas as pd
import numpy as np
from arch import arch_model
from datetime import datetime, timedelta
from scipy.stats import norm
from prettytable import PrettyTable

def garch_forecast(asset_symbol):
    """Perform GARCH analysis on stock data."""
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    print(f"\nFetching data for {asset_symbol} from {start_date} to {end_date}...")
    data = yf.download(asset_symbol, start=start_date, end=end_date)

    # Calculate Daily Returns (Percentage Change)
    data['Return'] = 100 * data['Adj Close'].pct_change()
    data.dropna(inplace=True)

    # Fit the GARCH(1,1) Model
    print(f"Fitting the GARCH(1,1) model for {asset_symbol}...")
    model = arch_model(data['Return'], vol='Garch', p=1, q=1, dist='normal')
    results = model.fit(update_freq=5, disp="off")

    # Forecast 1-day Volatility
    forecast = results.forecast(horizon=1)
    volatility = np.sqrt(forecast.variance.values[-1, 0])

    # Fetch Current Price
    ticker = yf.Ticker(asset_symbol)
    current_price = ticker.history(period="1d")['Close'].iloc[-1]

    # Calculate Moving Averages for Directional Bias
    data['SMA_20'] = data['Adj Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Adj Close'].rolling(window=50).mean()

    if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1]:
        bias = "Bullish"
        z_score = (current_price * 1.02 - current_price) / (current_price * (volatility / 100))
        probability_success = 1 - norm.cdf(z_score)  # Probability of upward movement
    else:
        bias = "Bearish"
        z_score = (current_price - current_price * 0.98) / (current_price * (volatility / 100))
        probability_success = norm.cdf(z_score)  # Probability of downward movement

    # Expected 1-day Price Range
    lower_bound = current_price * (1 - volatility / 100)
    upper_bound = current_price * (1 + volatility / 100)

    # Signal Strength: Combined Metric
    signal_strength = probability_success * volatility

    # Check if current price is outside expected 1-day range
    outside_range = not (lower_bound <= current_price <= upper_bound)

    return {
        'symbol': asset_symbol,
        'price': current_price,
        'probability_success': probability_success * 100,
        'volatility': volatility,
        'signal_strength': signal_strength,
        'bias': bias,
        'range': (lower_bound, upper_bound),
        'outside_range': outside_range
    }

def display_results(sorted_results):
    """Display results in PrettyTable format."""
    if not sorted_results:
        print("No valid stocks were analyzed.")
        return

    bullish = [res for res in sorted_results if res['bias'] == 'Bullish']
    bearish = [res for res in sorted_results if res['bias'] == 'Bearish']

    def create_table(title, results):
        table = PrettyTable()
        table.title = title
        table.field_names = [
            "Symbol", "Current Price", "Signal Strength", "Probability (%)", 
            "Volatility (%)", "Expected 1-day Range"
        ]
        for res in results:
            current_price = f"${res['price']:.2f}"
            # Highlight stocks where current price is outside the expected 1-day price range
            if res['outside_range']:
                current_price = f"**{current_price}**"
            table.add_row([
                res['symbol'], 
                current_price,
                f"{res['signal_strength']:.2f}", 
                f"{res['probability_success']:.2f}", 
                f"{res['volatility']:.2f}", 
                f"{res['range'][0]:.2f} - {res['range'][1]:.2f}"
            ])
        return table

    if bullish:
        print(create_table("Bullish Stocks", bullish))
    else:
        print("No bullish stocks found.")

    if bearish:
        print(create_table("Bearish Stocks", bearish))
    else:
        print("No bearish stocks found.")

def main_loop():
    stock_list = [
        'AAPL', 'TSLA', 'AMD', 'MSFT', 'SPY', 'QQQ', 'NVDA', 'AMZN', 'NIO', 
        'SOFI', 'F', 'PLTR', 'LCID', 'CHPT', 'AMC', 'PINS', 'AA', 'SNAP', 'BB',
        'XLF', 'IWM', 'EEM', 'ARKK', 'SLV', 'FXI', 'BABA', 'JD', 'RIOT', 
        'MARA', 'T', 'PBR', 'TLT', 'UNG', 'GDX', 'KRE', 'XOP', 'XLE', 'SPXL',
        'SOXS', 'UVXY', 'LABU', 'SQQQ', 'RDDT', 'NCLH'
    ]

    print("\nWelcome to UZI's GARCH analysis tool for trading short term options.\nhope you don't get REKT\nThe Current asset list for analysis is:")
    print(", ".join(stock_list))

    while True:
        new_stock = input("\nEnter a stock symbol to add (or 'done' to finish): ").strip().upper()
        if new_stock == 'DONE':
            break
        stock_list.append(new_stock)

    print("\nAnalyzing the following stocks:")
    print(", ".join(stock_list))

    results = []

    for stock in stock_list:
        try:
            result = garch_forecast(stock)
            results.append(result)
        except Exception as e:
            print(f"An error occurred for {stock}: {e}. Skipping...")

    sorted_results = sorted(results, key=lambda x: x['signal_strength'], reverse=True)
    display_results(sorted_results)

if __name__ == "__main__":
    main_loop()
