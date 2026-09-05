# Local Fundamental Data

Place local company fundamental CSV or Parquet files in this folder.

Supported columns include:

- `symbol`
- `date`
- `revenue`
- `net_profit`
- `eps`
- `pe_ratio`
- `pb_ratio`
- `roe`
- `roce`
- `debt`
- `debt_to_equity`
- `market_cap`
- `operating_margin`
- `net_margin`
- `free_cash_flow`
- `dividend_yield`

Alternate names such as `ticker`, `report_date`, `profit_after_tax`, `pat`, `p/e`, `p/b`, and `d/e` are normalized by the preprocessing layer.

The system uses only fields that exist. Missing values remain missing and are not replaced with zero.

Historical alignment rule: a fundamental record dated `T` may influence signals on date `T` or later only. Future-dated financial data is never used for earlier predictions or backtests.

`sample_fundamentals.csv` is synthetic sample data for tests and local development only.
