
import pandas as pd


# Valuation Factors
def calc_pe_inverse(df: pd.DataFrame) -> pd.Series:
    """
    Inverse PE ratio: 1 / PE
    Higher values indicate potentially undervalued stocks.
    """
    return 1 / df['pe_ttm']

def calc_pb_inverse(df: pd.DataFrame) -> pd.Series:
    """
    Inverse PB ratio: 1 / PB
    Used as a value factor, higher is better.
    """
    return 1 / df['pb']

def calc_dividend_yield(df: pd.DataFrame) -> pd.Series:
    """
    Dividend yield factor.
    Higher values indicate stronger income generation.
    """
    return df['dividendyield']


# Momentum Factor
def calc_momentum(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    N-day momentum: price percentage change over given window.
    Positive momentum indicates short-term strength.
    """
    return df.pct_change(periods=window).iloc[-1]


# Quality Factors (Optional)
def calc_roe(df: pd.DataFrame) -> pd.Series:
    """
    Return on equity (ROE).
    Measures profitability relative to equity.
    """
    return df['roe']
