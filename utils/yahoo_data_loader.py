import yfinance as yf
import pandas as pd
import os
from datetime import datetime

def fetch_yahoo_data(tickers, price_period="60d", price_interval="1d"):
    """
    Fetch Yahoo Finance data and save into project's data directory.
    """
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    factor_path = os.path.join(data_dir, "sample_stock_data.csv")
    price_path = os.path.join(data_dir, "close_prices.csv")

    
    records = []

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info

        try:
            close_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception:
            close_price = None

        row = {
            'ticker': ticker,
            'pe_ttm': info.get('trailingPE'),
            'pb': info.get('priceToBook'),
            'dividendyield': info.get('dividendYield'),
            'close': close_price,
            'date': datetime.today().strftime('%Y-%m-%d')
        }

        records.append(row)

    df_factors = pd.DataFrame(records)
    df_factors.dropna(inplace=True)
    df_factors.to_csv(factor_path, index=False)
    print(f"[✓] Factor data saved to: {factor_path}")

    
    close_prices = {}
    for ticker in tickers:
        hist = yf.Ticker(ticker).history(period=price_period, interval=price_interval)
        if not hist.empty:
            close_prices[ticker] = hist['Close']

    if close_prices:
        df_prices = pd.DataFrame(close_prices)
        df_prices.to_csv(price_path)
        print(f"[✓] Close price history saved to: {price_path}")

    return df_factors

if __name__ == "__main__":
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN']
    fetch_yahoo_data(tickers)
