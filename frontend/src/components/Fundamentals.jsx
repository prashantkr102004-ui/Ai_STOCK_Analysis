import React from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { formatCurrency, formatDate, formatNumber, formatPercent } from "../utils/formatters.js";

const METRICS = [
  ["revenue", "Revenue", "currency"],
  ["net_profit", "Net Profit", "currency"],
  ["eps", "EPS", "number"],
  ["pe_ratio", "P/E", "number"],
  ["pb_ratio", "P/B", "number"],
  ["roe", "ROE", "rawPercent"],
  ["roce", "ROCE", "rawPercent"],
  ["debt_to_equity", "Debt-to-Equity", "number"],
  ["operating_margin", "Operating Margin", "rawPercent"],
  ["net_margin", "Net Margin", "rawPercent"],
  ["free_cash_flow", "Free Cash Flow", "currency"],
  ["dividend_yield", "Dividend Yield", "rawPercent"]
];

function metricValue(value, kind) {
  if (kind === "currency") return formatCurrency(value);
  if (kind === "rawPercent") return formatPercent(value, true);
  return formatNumber(value, { maximumFractionDigits: 2 });
}

function ScoreBox({ label, value }) {
  if (value === null || value === undefined) return null;
  return (
    <div>
      <span>{label}</span>
      <strong>{formatNumber(value, { maximumFractionDigits: 2 })}</strong>
    </div>
  );
}

function FactorList({ title, items, negative = false }) {
  const Icon = negative ? XCircle : CheckCircle2;
  return (
    <div>
      <h3>{title}</h3>
      {!items?.length && <p className="mutedPanel">No major items detected from available fields.</p>}
      {!!items?.length && (
      <ul className={`reasonList ${negative ? "negativeList" : ""}`}>
        {items.map((item) => (
          <li key={item}>
            <Icon size={16} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
      )}
    </div>
  );
}

export default function Fundamentals({ fundamentals, history, loading, error }) {
  if (loading) return <section className="panel wide">Loading company fundamentals...</section>;
  if (error) return <section className="panel wide mutedPanel">{error}</section>;
  if (!fundamentals) return <section className="panel wide mutedPanel">No local fundamental data available for this stock.</section>;

  const visibleMetrics = METRICS.filter(([key]) => fundamentals.metrics?.[key] !== undefined && fundamentals.metrics?.[key] !== null);
  const chartRows = history?.length > 1 ? history : [];

  return (
    <section className="panel wide">
      <div className="sectionHeader">
        <h2>Company Fundamentals</h2>
        <span className={`pill ${fundamentals.fundamental_bias?.toLowerCase()}`}>{fundamentals.fundamental_bias}</span>
      </div>
      <div className="indicatorGrid">
        <div><span>Fundamental Score</span><strong>{formatNumber(fundamentals.fundamental_score, { maximumFractionDigits: 2 })}</strong></div>
        <div><span>Data Completeness</span><strong>{formatPercent(fundamentals.data_completeness, true)}</strong></div>
        <div><span>Latest Fundamental Date</span><strong>{formatDate(fundamentals.date)}</strong></div>
        <div><span>Business Risk</span><strong>{fundamentals.business_risk_level} - {formatNumber(fundamentals.business_risk_score, { maximumFractionDigits: 2 })}</strong></div>
      </div>

      <h3>Category Scores</h3>
      <div className="indicatorGrid">
        <ScoreBox label="Growth Score" value={fundamentals.growth_score} />
        <ScoreBox label="Profitability Score" value={fundamentals.profitability_score} />
        <ScoreBox label="Valuation Score" value={fundamentals.valuation_score} />
        <ScoreBox label="Balance Sheet Score" value={fundamentals.balance_sheet_score} />
        <ScoreBox label="Cash Flow Score" value={fundamentals.cash_flow_score} />
      </div>

      <h3>Metrics</h3>
      <div className="indicatorGrid">
        {visibleMetrics.map(([key, label, kind]) => (
          <div key={key}>
            <span>{label}</span>
            <strong>{metricValue(fundamentals.metrics[key], kind)}</strong>
          </div>
        ))}
      </div>

      <div className="factorColumns">
        <FactorList title="Company Strengths" items={fundamentals.strengths} />
        <FactorList title="Company Weaknesses" items={fundamentals.weaknesses} negative />
      </div>

      {chartRows.length > 1 && (
        <>
          <h3>Fundamental History</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartRows}>
              <CartesianGrid stroke="#203040" strokeDasharray="3 3" />
              <XAxis dataKey="date" stroke="#91a3b8" />
              <YAxis stroke="#91a3b8" />
              <Tooltip contentStyle={{ background: "#101922", border: "1px solid #263849" }} />
              <Legend />
              <Bar dataKey="revenue" name="Revenue" fill="#67e8f9" />
              <Bar dataKey="net_profit" name="Net Profit" fill="#34d399" />
              <Bar dataKey="eps" name="EPS" fill="#fbbf24" />
            </BarChart>
          </ResponsiveContainer>
        </>
      )}

      <small>Fundamental records are local historical data only. Records dated after a prediction date are excluded from that signal.</small>
    </section>
  );
}
