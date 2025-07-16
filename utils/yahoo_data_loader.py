import yfinance as yf
import pandas as pd
import os
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_root, "data")
os.makedirs(data_dir, exist_ok=True)


def fetch_yahoo_factors(tickers):
    """
    Fetch factor data (PE, PB, etc.) from Yahoo Finance and save to CSV.
    """
    today_str = datetime.today().strftime("%Y-%m-%d")
    factor_path = os.path.join(data_dir, f"sample_stock_data_{today_str}.csv")

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
            'date': today_str
        }
        records.append(row)

    df = pd.DataFrame(records)
    df.dropna(inplace=True)
    df.to_csv(factor_path, index=False)
    print(f"[Factor] Saved to: {factor_path}")
    return df


def fetch_close_prices(tickers, period="60d", interval="1d"):
    """
    Fetch close price history from Yahoo Finance and save to CSV.
    """
    today_str = datetime.today().strftime("%Y-%m-%d")
    price_path = os.path.join(data_dir, f"close_prices_{today_str}.csv")

    close_prices = {}
    for ticker in tickers:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        if not hist.empty:
            close_prices[ticker] = hist['Close']

    if close_prices:
        df_prices = pd.DataFrame(close_prices)
        df_prices.to_csv(price_path)
        print(f"[Price] Saved to: {price_path}")
        return df_prices
    else:
        print("[Price] No data fetched.")
        return pd.DataFrame()



if __name__ == "__main__":
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    fetch_yahoo_factors(tickers)
    fetch_close_prices(tickers)
