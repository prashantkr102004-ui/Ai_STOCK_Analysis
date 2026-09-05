import React from "react";
import { formatCurrency, formatPercent } from "../utils/formatters.js";

export default function BacktestCard({ backtest, loading, error, signal, model }) {
  if (loading) return <section className="panel">Loading latest backtest...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;
  if (!backtest) return <section className="panel mutedPanel">No saved backtest available. Run one below.</section>;

  const strategyWins = Number(backtest.strategy_return || 0) > Number(backtest.buy_hold_return || 0);
  return (
    <section className="panel wide">
      <div className="sectionHeader">
        <h2>Backtest Summary</h2>
        <span className="pill neutral">AI Strategy vs Buy & Hold</span>
      </div>
      <div className="indicatorGrid">
        <div><span>Initial Capital</span><strong>{formatCurrency(backtest.initial_capital)}</strong></div>
        <div><span>Final Capital</span><strong>{formatCurrency(backtest.final_capital)}</strong></div>
        <div><span>Total Profit/Loss</span><strong>{formatCurrency(backtest.total_profit_loss)}</strong></div>
        <div><span>Strategy Return</span><strong>{formatPercent(backtest.strategy_return)}</strong></div>
        <div><span>Buy & Hold Return</span><strong>{formatPercent(backtest.buy_hold_return)}</strong></div>
        <div><span>Trades</span><strong>{backtest.number_of_trades}</strong></div>
        <div><span>Winning Trades</span><strong>{backtest.winning_trades}</strong></div>
        <div><span>Losing Trades</span><strong>{backtest.losing_trades}</strong></div>
        <div><span>Win Rate</span><strong>{formatPercent(backtest.win_rate)}</strong></div>
        <div><span>Max Drawdown</span><strong>{formatPercent(backtest.max_drawdown)}</strong></div>
        <div><span>Sharpe</span><strong>{backtest.sharpe_ratio ?? "N/A"}</strong></div>
      </div>
      <p className="interpretation">
        {strategyWins
          ? "Strategy outperformed Buy & Hold during this historical period."
          : "Buy & Hold outperformed the model strategy during this historical period."}
      </p>
      <div className="contextPanel">
        <h3>Model Performance Context</h3>
        <div className="indicatorGrid">
          <div><span>Current Signal Confidence</span><strong>{formatPercent(signal?.confidence, true)}</strong></div>
          <div><span>Historical Test Accuracy</span><strong>{formatPercent(model?.accuracy)}</strong></div>
          <div><span>Backtest Strategy Return</span><strong>{formatPercent(backtest.strategy_return)}</strong></div>
          <div><span>Buy & Hold Return</span><strong>{formatPercent(backtest.buy_hold_return)}</strong></div>
          <div><span>Max Drawdown</span><strong>{formatPercent(backtest.max_drawdown)}</strong></div>
        </div>
      </div>
      <small>Historical backtests do not guarantee future market performance.</small>
    </section>
  );
}
