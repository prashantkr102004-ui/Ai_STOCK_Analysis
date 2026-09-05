import React from "react";
import { formatPercent, formatNumber } from "../utils/formatters.js";

function metric(value) {
  return value === null || value === undefined ? "N/A" : formatNumber(value, { maximumFractionDigits: 4 });
}

export default function ModelComparison({ comparison, loading, error }) {
  if (loading) return <section className="panel wide">Loading model comparison...</section>;
  if (error) return <section className="panel wide mutedPanel">{error}</section>;
  if (!comparison?.available) {
    return <section className="panel wide mutedPanel">{comparison?.message || "Model comparison has not been run yet."}</section>;
  }

  const production = comparison.models?.find((item) => item.production_model);

  return (
    <section className="panel wide">
      <div className="sectionHeader">
        <h2>Model Performance</h2>
        <span className="pill neutral">Offline Validation</span>
      </div>

      <div className="indicatorGrid">
        <div><span>Production Model</span><strong>{comparison.production_model_name || production?.model_name || "N/A"}</strong></div>
        <div><span>Accuracy</span><strong>{metric(production?.test_metrics?.accuracy)}</strong></div>
        <div><span>F1 Score</span><strong>{metric(production?.test_metrics?.f1)}</strong></div>
        <div><span>ROC-AUC</span><strong>{metric(production?.test_metrics?.roc_auc)}</strong></div>
        <div><span>Backtest Return</span><strong>{formatPercent(production?.backtest?.strategy_return)}</strong></div>
        <div><span>Sharpe Ratio</span><strong>{production?.backtest?.sharpe_ratio ?? "N/A"}</strong></div>
        <div><span>Maximum Drawdown</span><strong>{formatPercent(production?.backtest?.max_drawdown)}</strong></div>
        <div><span>Recommended Model</span><strong>{comparison.recommended_model || "N/A"}</strong></div>
      </div>

      {production?.overfitting_warning && <p className="warningNote">{production.overfitting_warning}</p>}
      <p className="interpretation">{comparison.selection_reason}</p>

      <div className="tableWrap modelTable">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Validation F1</th>
              <th>Test Accuracy</th>
              <th>Test F1</th>
              <th>ROC-AUC</th>
              <th>Strategy Return</th>
              <th>Sharpe</th>
              <th>Max Drawdown</th>
              <th>Threshold</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {comparison.models?.map((item) => (
              <tr key={item.model_key}>
                <td>{item.model_name}</td>
                <td>{metric(item.validation_metrics?.f1)}</td>
                <td>{metric(item.test_metrics?.accuracy)}</td>
                <td>{metric(item.test_metrics?.f1)}</td>
                <td>{metric(item.test_metrics?.roc_auc)}</td>
                <td>{formatPercent(item.backtest?.strategy_return)}</td>
                <td>{item.backtest?.sharpe_ratio ?? "N/A"}</td>
                <td>{formatPercent(item.backtest?.max_drawdown)}</td>
                <td>{item.selected_threshold ?? "N/A"}</td>
                <td>{item.production_model ? "CURRENT PRODUCTION MODEL" : item.overfitting_warning ? "Possible overfitting" : "Candidate"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <small>
        Classification metrics are historical validation/test results, not guaranteed market accuracy. Feature importance types differ by model and should not be compared as identical units.
      </small>
    </section>
  );
}
