import React from "react";
import { formatCompact, formatNumber, formatPercent } from "../utils/formatters.js";

const INDICATORS = [
  ["rsi", "RSI", "Momentum indicator from 0-100."],
  ["macd", "MACD", "Trend and momentum indicator."],
  ["macd_signal", "MACD Signal", "Signal line for MACD."],
  ["macd_histogram", "MACD Histogram", "Distance between MACD and signal."],
  ["sma_20", "SMA 20", "20-period average closing price."],
  ["sma_50", "SMA 50", "50-period average closing price."],
  ["sma_200", "SMA 200", "200-period average closing price."],
  ["ema_20", "EMA 20", "Recent-price weighted average."],
  ["ema_50", "EMA 50", "Recent-price weighted average."],
  ["atr", "ATR", "Measure of price volatility."],
  ["volume", "Volume", "Latest historical traded volume."],
  ["volume_ratio", "Volume Ratio", "Volume relative to recent average."],
  ["volatility", "Volatility", "Rolling return variability."]
];

function displayValue(key, value) {
  if (key === "volume") return formatCompact(value);
  if (key === "volatility") return formatPercent(value);
  return formatNumber(value, { maximumFractionDigits: 3 });
}

export default function IndicatorsGrid({ indicators, loading, error }) {
  if (loading) return <section className="panel">Loading technical indicators...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;

  return (
    <section className="panel wide">
      <h2>Technical Indicators</h2>
      <div className="indicatorGrid">
        {INDICATORS.map(([key, label, helper]) => (
          <div key={key}>
            <span>{label}</span>
            <strong>{displayValue(key, indicators?.[key])}</strong>
            <small>{helper}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
