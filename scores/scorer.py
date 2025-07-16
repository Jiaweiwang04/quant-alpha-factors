import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import pandas as pd
from factors import (
    calc_pe_inverse,
    calc_pb_inverse,
    calc_dividend_yield,
    calc_momentum
)


def zscore(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std()


def score_stocks(factor_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine all factor scores into a total_score.
    factor_df: contains pe_ttm, pb, dividendyield, close
    price_df: close price history for momentum
    """
    scores = pd.DataFrame(index=factor_df.index)

    scores['pe'] = zscore(calc_pe_inverse(factor_df))
    scores['pb'] = zscore(calc_pb_inverse(factor_df))
    scores['div'] = zscore(calc_dividend_yield(factor_df))

    scores['mom'] = zscore(calc_momentum(price_df))

    scores['total_score'] = scores.sum(axis=1)

    return scores



if __name__ == "__main__":
    
    factor_df = pd.read_csv("data/sample_stock_data.csv")
    factor_df = factor_df.set_index("ticker")

    
    price_df = pd.read_csv("data/close_prices.csv", index_col=0, parse_dates=True)
    price_df = price_df[factor_df.index]  

    
    result = score_stocks(factor_df, price_df)

    
    date_str = datetime.today().strftime('%Y-%m-%d')
    output_path = os.path.join("docs", f"factor_scores_{date_str}.csv")
    os.makedirs("docs", exist_ok=True)
    result.to_csv(output_path)

    
    print("\n Score file saved to:", output_path)
    print("\nTop Scored Stocks:\n")
    print(result.sort_values(by="total_score", ascending=False).round(3))