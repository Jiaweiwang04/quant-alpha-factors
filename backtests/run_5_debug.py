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

# ======== 参数设置 ======== #
RUN_DATE = "2025-07-16"  # 每次运行日
TICKERS = ["AAPL", "MSFT", "GOOGL", "META"]
PRICE_DIR = "data"
FACTOR_DIR = "docs"
LOOKBACK_DAYS = 5
TOP_N = 2

def calculate_manual_return(tickers, price_df, start_dt, end_dt):
    """手动计算收益率作为备选方案"""
    try:
        start_date = pd.to_datetime(start_dt.date())
        end_date = pd.to_datetime(end_dt.date())
        
        returns = []
        for ticker in tickers:
            ticker_col = ticker.lower()
            if ticker_col not in price_df.columns:
                continue
                
            df = price_df[["date", ticker_col]].copy()
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
            
            if len(df) < 2:
                continue
                
            start_price = df.iloc[0][ticker_col]
            end_price = df.iloc[-1][ticker_col]
            
            if start_price > 0 and not pd.isna(start_price) and not pd.isna(end_price):
                ticker_return = (end_price - start_price) / start_price
                returns.append(ticker_return)
                print(f"  {ticker}: {start_price:.2f} -> {end_price:.2f} ({ticker_return:.2%})")
        
        if returns:
            avg_return = sum(returns) / len(returns) * 100
            return avg_return
        else:
            return None
    except Exception as e:
        print(f"手动计算失败: {e}")
        return None

# ======== 步骤 1: 回测过去五天持仓表现（使用五天前打分选股） ======== #
rebalance_dt = datetime.strptime(RUN_DATE, "%Y-%m-%d") - timedelta(days=LOOKBACK_DAYS)
score_file = f"{FACTOR_DIR}/factor_scores_{rebalance_dt.strftime('%Y-%m-%d')}.csv"
print(f"\n[回测] 使用 {score_file} 中的打分前 top{TOP_N} 股票，模拟 {rebalance_dt.date()} ~ {datetime.strptime(RUN_DATE, '%Y-%m-%d') - timedelta(days=1)} 的收益")

if not os.path.exists(score_file):
    raise FileNotFoundError(f"找不到打分文件: {score_file}")

score_df = pd.read_csv(score_file)
score_df.set_index("ticker", inplace=True)
holding_tickers = score_df.sort_values(by="total_score", ascending=False).head(TOP_N).index.tolist()
print(f"选中的股票: {holding_tickers}")

start_dt = rebalance_dt
end_dt = datetime.strptime(RUN_DATE, "%Y-%m-%d") - timedelta(days=1)
print(f"回测时间范围: {start_dt.date()} 到 {end_dt.date()}")

cerebro = bt.Cerebro()
cerebro.broker.set_cash(1000000.0)
start_cash = 1000000.0

price_file = os.path.join(PRICE_DIR, f"close_prices_{RUN_DATE}.csv")
print(f"读取价格文件: {price_file}")

price_df = pd.read_csv(price_file, parse_dates=["Date"])
# 处理时区问题 - 移除时区信息
price_df["Date"] = price_df["Date"].dt.tz_localize(None)
price_df.columns = [col.lower() if col != "Date" else "date" for col in price_df.columns]

print(f"价格数据日期范围: {price_df['date'].min()} 到 {price_df['date'].max()}")
print(f"价格数据列名: {price_df.columns.tolist()}")

# 检查每个股票的数据
data_count = 0
for ticker in holding_tickers:
    ticker_col = ticker.lower()
    if ticker_col not in price_df.columns:
        print(f"❌ 缺失 {ticker} 收盘价数据，跳过")
        continue

    df = price_df[["date", ticker_col]].copy()
    df.rename(columns={ticker_col: "close"}, inplace=True)
    
    # 修复日期过滤逻辑
    start_date = pd.to_datetime(start_dt.date())
    end_date = pd.to_datetime(end_dt.date())
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    
    print(f"{ticker} 在回测期间的数据点数: {len(df)}")
    if df.empty:
        print(f"❌ {ticker} 在回测期间没有数据")
        continue
    
    # 检查数据质量
    if df["close"].isna().any():
        print(f"⚠️ {ticker} 有缺失的收盘价数据")
        df = df.dropna()
    
    if df.empty:
        print(f"❌ {ticker} 清理后没有有效数据")
        continue
    
    print(f"✅ {ticker} 数据范围: {df['date'].min()} 到 {df['date'].max()}")
    print(f"   收盘价范围: {df['close'].min():.2f} 到 {df['close'].max():.2f}")
    print(f"   数据样本: {df.head(2)}")
    
    # 确保索引是datetime类型
    df.set_index("date", inplace=True)
    
    # 添加必要的OHLV列
    df['open'] = df['close']
    df['high'] = df['close'] 
    df['low'] = df['close']
    df['volume'] = 1000  # 虚拟交易量
    
    # 确保列的顺序正确
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    data = bt.feeds.PandasData(dataname=df, name=ticker, openinterest=None)
    cerebro.adddata(data)
    data_count += 1

print(f"\n总共加载了 {data_count} 个股票数据")

class HoldFixedStrategy(bt.Strategy):
    def __init__(self):
        self.bought = False
        self.data_names = [d._name for d in self.datas]
        self.orders = []
        print(f"策略初始化，数据源: {self.data_names}")

    def next(self):
        if not self.bought:
            total_value = self.broker.getvalue()
            weight = 1.0 / len(self.datas)
            print(f"第一天买入，总资金: ${total_value:,.2f}, 每股权重: {weight:.2%}")
            
            # 清空之前的订单
            self.orders = []
            
            for i, d in enumerate(self.datas):
                current_price = d.close[0]
                print(f"检查 {d._name}: 价格={current_price}")
                
                if current_price > 0 and not pd.isna(current_price):  # 确保价格有效
                    target_value = total_value * weight
                    size = int(target_value / current_price)  # 使用整数股数
                    
                    if size > 0:
                        order = self.buy(data=d, size=size)
                        self.orders.append(order)
                        actual_value = size * current_price
                        print(f"买入 {d._name}: 价格=${current_price:.2f}, 数量={size}, 实际金额=${actual_value:,.2f}")
                    else:
                        print(f"⚠️ {d._name} 计算的股数为0")
                else:
                    print(f"⚠️ {d._name} 价格无效: {current_price}")
            
            self.bought = True
        
        # 每天打印持仓信息
        if len(self.datas) > 0:
            current_date = self.datas[0].datetime.date(0)
            total_value = self.broker.getvalue()
            cash = self.broker.getcash()
            
            if hasattr(self, 'last_print_date') and self.last_print_date == current_date:
                return
            self.last_print_date = current_date
            
            # 计算持仓价值
            position_value = 0
            for d in self.datas:
                pos = self.getposition(d)
                if pos.size > 0:
                    pos_value = pos.size * d.close[0]
                    position_value += pos_value
                    print(f"  {d._name}: 持仓{pos.size}股, 价格${d.close[0]:.2f}, 价值${pos_value:,.2f}")
            
            print(f"{current_date}: 总资产=${total_value:,.2f}, 现金=${cash:,.2f}, 持仓价值=${position_value:,.2f}")

cerebro.addstrategy(HoldFixedStrategy)
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='daily_returns')

if len(cerebro.datas) == 0:
    print("❌ 没有加载任何数据，无法执行回测。请检查:")
    print("1. 价格数据文件是否存在")
    print("2. 股票代码是否正确")
    print("3. 日期范围是否有数据")
    sys.exit(1)

print(f"\n开始回测...")
print(f"Cerebro数据源数量: {len(cerebro.datas)}")
print(f"初始资金: ${start_cash:,.2f}")

# 运行回测前的最后检查
for i, data in enumerate(cerebro.datas):
    print(f"数据源 {i}: {data._name}, 长度: {len(data)}")

result = cerebro.run()

# 获取最终结果
final_value = cerebro.broker.getvalue()
cash = cerebro.broker.getcash()

print(f"\n=== 回测结果 ===")
print(f"初始资金: ${start_cash:,.2f}")
print(f"最终资金: ${final_value:,.2f}")
print(f"最终现金: ${cash:,.2f}")

# 检查结果是否有效
if pd.isna(final_value) or final_value <= 0:
    print("❌ 回测结果无效，可能原因:")
    print("1. 数据质量问题")
    print("2. 订单执行失败")
    print("3. Backtrader配置问题")
    
    # 尝试简单的收益率计算
    print("\n尝试手动计算收益率...")
    manual_return = calculate_manual_return(holding_tickers, price_df, start_dt, end_dt)
    if manual_return is not None:
        print(f"手动计算收益率: {manual_return:.2f}%")
    
    returns = 0
else:
    returns = (final_value - start_cash) / start_cash * 100
    print(f"回测收益率: {returns:.2f}%")

# 保存每日收益率
daily_returns = result[0].analyzers.daily_returns.get_analysis()
if daily_returns:
    returns_df = pd.Series(daily_returns).rename("daily_return").to_frame()
    returns_df.index.name = "date"
    returns_df["cum_return"] = (1 + returns_df["daily_return"]).cumprod() - 1
    output_path = f"docs/returns_{RUN_DATE}.csv"
    returns_df.to_csv(output_path)
    print(f"已保存收益曲线: {output_path}")
else:
    print("⚠️ 没有获取到每日收益率数据")

# ======== 步骤 2: 获取当天因子并打分 ======== #
print(f"\n[打分] 获取 {RUN_DATE} 实时数据...")
try:
    factor_rows = fetch_yahoo_factors(TICKERS)
    close_df = fetch_close_prices(TICKERS)

    factor_df = pd.DataFrame(factor_rows).set_index("ticker")
    score_df = score_stocks(factor_df, close_df)

    score_path = os.path.join(FACTOR_DIR, f"factor_scores_{RUN_DATE}.csv")
    score_df.to_csv(score_path)
    print(f"保存打分文件: {score_path}")

    selected = score_df.sort_values(by="total_score", ascending=False).head(TOP_N)
    holding = list(selected.index)
    print(f"\n[调仓结果] 等权买入：{holding}")
    
    print("\n当日打分结果:")
    print(score_df.sort_values(by="total_score", ascending=False).round(3))
    
except Exception as e:
    print(f"❌ 获取当日数据失败: {e}")
    print("这可能是因为:")
    print("1. 网络连接问题")
    print("2. Yahoo Finance API限制")
    print("3. 股票代码不存在")