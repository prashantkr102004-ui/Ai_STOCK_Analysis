import React from "react";
import { formatNumber } from "../utils/formatters.js";

export default function FeatureImportance({ features, loading, error }) {
  if (loading) return <section className="panel">Loading feature importance...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;
  if (!features?.length) return <section className="panel mutedPanel">No feature importance available.</section>;

  const max = Math.max(...features.map((item) => item.importance));
  return (
    <section className="panel">
      <h2>Top Model Features</h2>
      <div className="featureList">
        {features.slice(0, 10).map((item) => (
          <div key={item.feature}>
            <div>
              <span>{item.feature}</span>
              <strong>{formatNumber(item.importance, { maximumFractionDigits: 4 })}</strong>
            </div>
            <div className="barTrack">
              <div className="barFill amber" style={{ width: `${(item.importance / max) * 100}%` }} />
            </div>
            {item.explanation && <small>{item.explanation}</small>}
          </div>
        ))}
      </div>
      <small>Feature importance indicates how strongly the model relies on each feature; it does not prove causation.</small>
    </section>
  );
}
