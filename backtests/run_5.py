import os
import json
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backtrader as bt
import pandas as pd
from scores.scorer import score_stocks
from utils.yahoo_data_loader import fetch_close_prices, fetch_yahoo_factors
from strategies.equal_weight import EqualWeightScoringStrategy


RUN_DATE = "2025-07-16"  
TICKERS = ["AAPL", "MSFT", "GOOGL", "META"]
PRICE_DIR = "data"
FACTOR_DIR = "docs"
LOOKBACK_DAYS = 5
TOP_N = 2


rebalance_dt = datetime.strptime(RUN_DATE, "%Y-%m-%d") - timedelta(days=LOOKBACK_DAYS)
score_file = f"{FACTOR_DIR}/factor_scores_{rebalance_dt.strftime('%Y-%m-%d')}.csv"

if not os.path.exists(score_file):
    raise FileNotFoundError(f"can not file: {score_file}")

score_df = pd.read_csv(score_file)
score_df.set_index("ticker", inplace=True)
holding_tickers = score_df.sort_values(by="total_score", ascending=False).head(TOP_N).index.tolist()

start_dt = rebalance_dt
end_dt = datetime.strptime(RUN_DATE, "%Y-%m-%d") - timedelta(days=1)

cerebro = bt.Cerebro()
cerebro.broker.set_cash(1000000.0)
start_cash = 1000000.0

price_file = os.path.join(PRICE_DIR, f"close_prices_{RUN_DATE}.csv")
price_df = pd.read_csv(price_file, parse_dates=["Date"])

price_df.columns = [col.lower() for col in price_df.columns]
price_df["date"] = price_df["date"].dt.tz_localize(None)

for ticker in holding_tickers:
    ticker_col = ticker.lower()
    if ticker_col not in price_df.columns:
        print(f" lack {ticker} close price，skip")
        continue

    df = price_df[["date", ticker_col]].copy()
    df.rename(columns={ticker_col: "close"}, inplace=True)
    
    
    start_date = pd.to_datetime(start_dt.date())
    end_date = pd.to_datetime(end_dt.date())
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    
    if df.empty:
        continue

    df.set_index("date", inplace=True)

    df['open'] = df['close']
    df['high'] = df['close'] 
    df['low'] = df['close']
    df['volume'] = 1000  
    df = df[['open', 'high', 'low', 'close', 'volume']]

    data = bt.feeds.PandasData(dataname=df, name=ticker, openinterest=-1)
    cerebro.adddata(data)

cerebro.addstrategy(EqualWeightScoringStrategy)
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='daily_returns')


result = cerebro.run()
final_value = cerebro.broker.getvalue()
cash = cerebro.broker.getcash()
returns = (final_value - start_cash) / start_cash * 100

daily_returns = result[0].analyzers.daily_returns.get_analysis()
if daily_returns:
    returns_df = pd.Series(daily_returns).rename("daily_return").to_frame()
    returns_df.index.name = "date"
    returns_df["cum_return"] = (1 + returns_df["daily_return"]).cumprod() - 1
    output_path = f"docs/returns_{RUN_DATE}.csv"
    returns_df.to_csv(output_path)
    print(f"profits result saved to : {output_path}")
else:
    print("did not get and datas")



print(f"\n[score] get {RUN_DATE} data")
factor_rows = fetch_yahoo_factors(TICKERS)
close_df = fetch_close_prices(TICKERS)

factor_df = pd.DataFrame(factor_rows).set_index("ticker")
score_df = score_stocks(factor_df, close_df)

score_path = os.path.join(FACTOR_DIR, f"factor_scores_{RUN_DATE}.csv")
score_df.to_csv(score_path)
print(f" score file saved to: {score_path}")

selected = score_df.sort_values(by="total_score", ascending=False).head(TOP_N)
holding = list(selected.index)
print(f"\n[result] equal weight buy：{holding}")
