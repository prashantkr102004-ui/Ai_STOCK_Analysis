import React from "react";
import { formatCurrency, formatPercent } from "../utils/formatters.js";

export default function TradeTable({ trades, loading, error }) {
  if (loading) return <section className="panel wide">Loading trade history...</section>;
  if (error) return <section className="panel wide mutedPanel">{error}</section>;
  if (!trades?.length) return <section className="panel wide mutedPanel">No trade history available.</section>;

  return (
    <section className="panel wide">
      <div className="sectionHeader">
        <h2>Trade History</h2>
        <span className="pill neutral">{trades.length} trades</span>
      </div>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Trade ID</th>
              <th>Signal Date</th>
              <th>Entry Date</th>
              <th>Entry Price</th>
              <th>Exit Date</th>
              <th>Exit Price</th>
              <th>Shares</th>
              <th>Profit/Loss</th>
              <th>Return %</th>
            </tr>
          </thead>
          <tbody>
            {trades.slice(0, 100).map((trade) => (
              <tr key={trade.trade_id}>
                <td>{trade.trade_id}</td>
                <td>{trade.signal_date}</td>
                <td>{trade.entry_date}</td>
                <td>{formatCurrency(trade.entry_price)}</td>
                <td>{trade.exit_date}</td>
                <td>{formatCurrency(trade.exit_price)}</td>
                <td>{trade.shares}</td>
                <td className={trade.profit_loss >= 0 ? "positiveText" : "negativeText"}>{formatCurrency(trade.profit_loss)}</td>
                <td>{formatPercent(trade.return_percentage, true)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {trades.length > 100 && <small>Showing first 100 trades. The full log is available from the API.</small>}
    </section>
  );
}
