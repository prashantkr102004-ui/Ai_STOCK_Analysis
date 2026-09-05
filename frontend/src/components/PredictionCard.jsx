import React from "react";
import { formatPercent, formatProbability } from "../utils/formatters.js";

function ConfidenceBar({ label, value }) {
  const percent = Math.max(0, Math.min(100, Number(value || 0) * 100));
  return (
    <div className="confidenceRow">
      <div>
        <span>{label}</span>
        <strong>{formatProbability(value)}</strong>
      </div>
      <div className="barTrack" aria-label={`${label} ${percent.toFixed(2)} percent`}>
        <div className="barFill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

export default function PredictionCard({ prediction, loading, error }) {
  if (loading) return <section className="panel">Loading prediction...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;
  if (!prediction) return <section className="panel mutedPanel">Model prediction unavailable.</section>;

  return (
    <section className="panel">
      <div className="sectionHeader">
        <h2>AI Model Analysis</h2>
        <span className={`pill ${prediction.prediction?.toLowerCase()}`}>{prediction.prediction}</span>
      </div>
      <div className="predictionText">{prediction.prediction}</div>
      <p>Model Confidence: {formatPercent(prediction.confidence, true)}</p>
      <div className="confidenceStack">
        <ConfidenceBar label="UP" value={prediction.probability_up} />
        <ConfidenceBar label="DOWN" value={prediction.probability_down} />
      </div>
      <p>Model: {prediction.model}</p>
      <p>Version: {prediction.model_version}</p>
      <small>Model output based on historical patterns; not financial advice.</small>
    </section>
  );
}
