import React from "react";

export default function IndicatorCard({ indicators }) {
  const rows = Object.entries(indicators || {}).filter(([key]) => key !== "symbol");
  return (
    <section className="panel">
      <h2>Technical Indicators</h2>
      <div className="indicatorGrid">
        {rows.map(([key, value]) => (
          <div key={key}>
            <span>{key}</span>
            <strong>{value == null ? "N/A" : Number(value).toFixed(3)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
