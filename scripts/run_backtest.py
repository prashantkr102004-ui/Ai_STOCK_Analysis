import json
import argparse

import pandas as pd

import _bootstrap  # noqa: F401
from backend.app.core.config import get_settings
from ml.backtesting.backtest import run_backtest


def print_summary(result: dict):
    print("AI MARKETGUARD BACKTEST")
    print("")
    print(f"Symbol: {result['symbol']}")
    print("")
    print(f"Initial Capital: {result['initial_capital']:,.2f}")
    print(f"Final Capital: {result['final_capital']:,.2f}")
    print("")
    print(f"Strategy Return: {result['strategy_return_pct']:.2f}%")
    print(f"Buy & Hold Return: {result['buy_hold_return_pct']:.2f}%")
    print("")
    print(f"Trades: {result['number_of_trades']}")
    print(f"Win Rate: {result['win_rate_pct']:.2f}%")
    print("")
    print(f"Max Drawdown: {result['max_drawdown_pct']:.2f}%")
    print(f"Sharpe Ratio: {result['sharpe_ratio']}")
    print("")
    print(f"Trade Log: {result.get('trade_log_path')}")
    print(f"Equity Curve: {result.get('equity_curve_path')}")


def main():
    parser = argparse.ArgumentParser(description="Run AI MarketGuard backtests.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbol", help="Run one symbol, for example RELIANCE.")
    group.add_argument("--all", action="store_true", help="Run every available stock independently.")
    parser.add_argument("--start-date", help="Optional start date, YYYY-MM-DD.")
    parser.add_argument("--end-date", help="Optional end date, YYYY-MM-DD.")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital.")
    parser.add_argument("--transaction-cost", type=float, default=0.001, help="Per-side transaction cost.")
    parser.add_argument("--slippage", type=float, default=0.0, help="Per-side slippage assumption.")
    args = parser.parse_args()

    settings = get_settings()
    source = settings.processed_path / "all_stocks_features.parquet"
    if not source.exists():
        raise FileNotFoundError("Processed features not found. Run python scripts/calculate_features.py first.")
    processed = pd.read_parquet(source)

    symbols = sorted(processed["Symbol"].unique()) if args.all else [args.symbol.upper()]
    results = []
    for symbol in symbols:
        result = run_backtest(
            processed,
            symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.capital,
            transaction_cost=args.transaction_cost,
            slippage=args.slippage,
            model_dir="models",
        )
        results.append({key: value for key, value in result.items() if key != "equity_curve"})
        print_summary(result)
        print("")

    if args.all:
        output = settings.processed_path / "all_backtests_summary.json"
        output.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
