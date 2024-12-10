import yfinance as yf
import pandas as pd
import numpy as np
from arch import arch_model
from datetime import datetime, timedelta
from scipy.stats import norm

def fetch_data(asset_symbol, lookback_days=365):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    data = yf.download(asset_symbol, start=start_date, end=end_date)
    return data

def calculate_returns(data):
    data['Return'] = 100 * data['Adj Close'].pct_change()
    data.dropna(inplace=True)
    return data

def fit_garch_model(returns):
    model = arch_model(returns, vol='Garch', p=1, q=1, dist='normal')
    results = model.fit(update_freq=5, disp='off')
    return results

def forecast_volatility(results, horizon=1):
    forecast = results.forecast(horizon=horizon)
    vol = np.sqrt(forecast.variance.values[-1, 0])
    return vol

def fetch_current_price(asset_symbol):
    ticker = yf.Ticker(asset_symbol)
    current_data = ticker.history(period="1d")
    if current_data.empty:
        return None
    return current_data['Close'].iloc[-1]

def calculate_bias_and_probability(data, current_price, volatility):
    data['SMA_20'] = data['Adj Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Adj Close'].rolling(window=50).mean()

    # Default probability and bias
    bias = "Neutral"
    probability_success = 0.5

    if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1]:
        bias = "Bullish"
        z_score = (current_price * 1.02 - current_price) / (current_price * (volatility / 100))
        probability_success = 1 - norm.cdf(z_score)  # Probability of upward movement
    elif data['SMA_20'].iloc[-1] < data['SMA_50'].iloc[-1]:
        bias = "Bearish"
        z_score = (current_price - current_price * 0.98) / (current_price * (volatility / 100))
        probability_success = norm.cdf(z_score)  # Probability of downward movement
    else:
        bias = "Neutral"
        probability_success = 0.5

    return bias, probability_success

def garch_forecast(asset_symbol):
    data = fetch_data(asset_symbol, lookback_days=365)
    if data.empty:
        raise ValueError("No data returned. Check symbol or date range.")

    data = calculate_returns(data)
    results = fit_garch_model(data['Return'])
    volatility = forecast_volatility(results, horizon=1)
    current_price = fetch_current_price(asset_symbol)

    if current_price is None:
        raise ValueError("Could not fetch current price.")

    bias, probability_success = calculate_bias_and_probability(data, current_price, volatility)

    lower_bound = current_price * (1 - volatility / 100)
    upper_bound = current_price * (1 + volatility / 100)

    signal_strength = probability_success * volatility

    outside_range = not (lower_bound <= current_price <= upper_bound)

    return {
        'symbol': asset_symbol,
        'price': current_price,
        'probability_success': probability_success * 100,
        'volatility': volatility,
        'signal_strength': signal_strength,
        'bias': bias,
        'range': (lower_bound, upper_bound),
        'outside_range': outside_range,
        'garch_results': results,
        'data': data
    }
