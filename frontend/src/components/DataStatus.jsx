import React from "react";
import { formatDate, formatNumber } from "../utils/formatters.js";

export default function DataStatus({ status, loading, error }) {
  if (loading) return <section className="panel">Loading dataset status...</section>;
  if (error) return <section className="panel mutedPanel">{error}</section>;
  if (!status) return <section className="panel mutedPanel">Dataset status unavailable.</section>;

  const rows = [
    ["Available Stocks", formatNumber(status.number_of_stocks)],
    ["Historical Records", formatNumber(status.total_historical_records)],
    ["Earliest Date", formatDate(status.earliest_available_date)],
    ["Latest Date", formatDate(status.latest_available_date)],
    ["Processed Files", formatNumber(status.number_of_processed_files)],
    ["Last Processing Time", formatDate(status.last_processing_time)]
  ];

  return (
    <section className="panel">
      <h2>Dataset Status</h2>
      <div className="kvList">
        {rows.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
