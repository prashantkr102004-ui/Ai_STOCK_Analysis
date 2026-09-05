import React from "react";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { formatPercent } from "../utils/formatters.js";

function ScoreTile({ label, value, suffix = "" }) {
  const numeric = Number(value);
  const width = Number.isFinite(numeric) ? Math.max(0, Math.min(100, numeric)) : 0;
  return (
    <div className="scoreTile">
      <div>
        <span>{label}</span>
        <strong>{Number.isFinite(numeric) ? `${numeric.toFixed(2)}${suffix}` : "N/A"}</strong>
      </div>
      <div className="barTrack">
        <div className="barFill" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function FactorList({ title, items, type }) {
  if (!items?.length) return null;
  const Icon = type === "negative" ? XCircle : CheckCircle2;
  return (
    <div>
      <h3>{title}</h3>
      <ul className={`reasonList ${type === "negative" ? "negativeList" : ""}`}>
        {items.map((reason) => (
          <li key={reason}>
            <Icon size={16} />
            <span>{reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SignalCard({ signal, loading, error }) {
  if (loading) return <section className="panel">Loading signal...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;
  if (!signal) return <section className="panel mutedPanel">No signal available.</section>;

  return (
    <section className="panel">
      <div className="sectionHeader">
        <h2>Model-Based Signal</h2>
        <span className={`pill ${signal.signal?.toLowerCase()}`}>{signal.signal}</span>
      </div>
      <p className="bigNumber">{signal.signal} - {signal.confidence_level || "Confidence Pending"}</p>
      <p>Confidence: {formatPercent(signal.confidence, true)}</p>
      {signal.confidence_level?.toLowerCase().includes("low") && (
        <div className="warningNote">
          <AlertTriangle size={16} />
          <span>Model confidence is weak. Interpret this signal cautiously.</span>
        </div>
      )}
      <div className="scoreGrid">
        <ScoreTile label="ML Score" value={signal.ml_score} />
        <ScoreTile label="Technical Score" value={signal.technical_score} />
        {signal.sentiment_signal_score !== null && signal.sentiment_signal_score !== undefined && (
          <ScoreTile label="Sentiment Score" value={signal.sentiment_signal_score} />
        )}
        {signal.fundamental_score !== null && signal.fundamental_score !== undefined && (
          <ScoreTile label={`Fundamental Score (${signal.fundamental_bias || "N/A"})`} value={signal.fundamental_score} />
        )}
        <ScoreTile label="Combined Score" value={signal.combined_score} />
        <ScoreTile label={`Risk Score (${signal.risk_level || "N/A"})`} value={signal.risk_score} />
        {signal.business_risk_score !== null && signal.business_risk_score !== undefined && (
          <ScoreTile label={`Business Risk (${signal.business_risk_level || "N/A"})`} value={signal.business_risk_score} />
        )}
      </div>
      <h3>Why this signal?</h3>
      <p className="interpretation">{signal.summary}</p>
      <FactorList title="Supporting Factors" items={signal.positive_factors || signal.reasons} />
      <FactorList title="Contradicting Factors" items={signal.negative_factors} type="negative" />
      {!signal.positive_factors && (
      <ul className="reasonList">
        {signal.reasons.map((reason) => (
          <li key={reason}>
            <CheckCircle2 size={16} />
            <span>{reason}</span>
          </li>
        ))}
      </ul>
      )}
      <small>{signal.description}</small>
    </section>
  );
}
