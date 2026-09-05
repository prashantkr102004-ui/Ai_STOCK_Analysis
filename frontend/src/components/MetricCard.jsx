import React from "react";

export default function MetricCard({ label, value, tone = "neutral", helper }) {
  return (
    <section className={`metricCard ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {helper && <small>{helper}</small>}
    </section>
  );
}
