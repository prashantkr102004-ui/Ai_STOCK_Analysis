import React from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export default function EquityCurveChart({ data, loading, error }) {
  if (loading) return <section className="panel wide chartPanel">Loading equity curve...</section>;
  if (error) return <section className="panel wide mutedPanel">{error}</section>;
  if (!data?.length) return <section className="panel wide mutedPanel">No equity curve available.</section>;

  return (
    <section className="panel wide chartPanel">
      <h2>Equity Curve</h2>
      <p className="section-note">AI Strategy vs Buy & Hold</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
          <XAxis dataKey="date" minTickGap={36} stroke="#91a3b8" />
          <YAxis stroke="#91a3b8" domain={["auto", "auto"]} />
          <Tooltip contentStyle={{ background: "#101820", border: "1px solid #2a394a" }} />
          <Line type="monotone" dataKey="total_equity" stroke="#34d399" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="buy_hold_equity" stroke="#fbbf24" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
