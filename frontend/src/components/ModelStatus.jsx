import React from "react";
import { formatDate, formatNumber } from "../utils/formatters.js";

export default function ModelStatus({ model, loading, error }) {
  if (loading) return <section className="panel">Loading model status...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;
  if (!model?.trained) return <section className="panel mutedPanel">{model?.message || "Model not trained."}</section>;

  const metrics = [
    ["Model", model.model_name],
    ["Version", model.model_version],
    ["Training Date", formatDate(model.training_date)],
    ["Feature Count", model.feature_count],
    ["Training Samples", formatNumber(model.training_samples)],
    ["Validation Samples", formatNumber(model.validation_samples)],
    ["Test Samples", formatNumber(model.test_samples)],
    ["Accuracy", formatNumber(model.accuracy, { maximumFractionDigits: 4 })],
    ["Precision", formatNumber(model.precision, { maximumFractionDigits: 4 })],
    ["Recall", formatNumber(model.recall, { maximumFractionDigits: 4 })],
    ["F1 Score", formatNumber(model.f1, { maximumFractionDigits: 4 })],
    ["ROC-AUC", formatNumber(model.roc_auc, { maximumFractionDigits: 4 })]
  ];

  return (
    <section className="panel">
      <h2>Model Information</h2>
      <div className="kvList">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value ?? "N/A"}</strong>
          </div>
        ))}
      </div>
      <small>Metrics are historical test metrics.</small>
    </section>
  );
}
