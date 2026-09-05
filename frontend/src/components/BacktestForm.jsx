import React from "react";
import { Play } from "lucide-react";

export default function BacktestForm({ form, onChange, onSubmit, running, error }) {
  return (
    <section className="panel wide">
      <div className="sectionHeader">
        <h2>Run Backtest</h2>
        <span className="pill neutral">Manual Run</span>
      </div>
      <form className="backtestForm" onSubmit={onSubmit}>
        <label>
          Start Date
          <input type="date" value={form.start_date} onChange={(event) => onChange("start_date", event.target.value)} />
        </label>
        <label>
          End Date
          <input type="date" value={form.end_date} onChange={(event) => onChange("end_date", event.target.value)} />
        </label>
        <label>
          Initial Capital
          <input type="number" min="1" step="1000" value={form.initial_capital} onChange={(event) => onChange("initial_capital", event.target.value)} />
        </label>
        <label>
          Transaction Cost
          <input type="number" min="0" step="0.0001" value={form.transaction_cost} onChange={(event) => onChange("transaction_cost", event.target.value)} />
        </label>
        <label>
          Slippage
          <input type="number" min="0" step="0.0001" value={form.slippage} onChange={(event) => onChange("slippage", event.target.value)} />
        </label>
        <button type="submit" disabled={running}>
          <Play size={16} />
          {running ? "Running backtest..." : "Run Backtest"}
        </button>
      </form>
      {error && <p className="formError">{error}</p>}
    </section>
  );
}
