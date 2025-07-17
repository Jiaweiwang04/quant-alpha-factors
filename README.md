# QUANT-ALPHA-FACTORS

This project implements an equal-weight, multi-factor stock selection strategy.  
Every five trading days, the strategy runs a full cycle of backtesting and portfolio rebalancing.

The core idea is to rank stocks using multiple fundamental and market-based factors, and to construct a top-N portfolio based on the aggregated score.

This project helps us understand the **basic structure and workflow** of a multi-factor equity strategy, including:

- Factor construction (e.g., PE, PB, ROE, Momentum)
- Standardization and scoring
- Portfolio construction (equal weight)
- Rolling backtest with periodic rebalancing

It serves as a foundation for building more advanced alpha models and execution frameworks in the future.

---

**Author**  
Jiawei Wang  
Undergraduate, Mathematics, University College London
