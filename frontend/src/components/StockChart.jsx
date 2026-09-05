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

export default function StockChart({ data, loading, error, range }) {
  if (loading) return <section className="panel chartPanel">Loading historical data...</section>;
  if (error) return <section className="panel chartPanel mutedPanel">{error}</section>;
  if (!data?.length) return <section className="panel chartPanel mutedPanel">Historical data unavailable.</section>;

  return (
    <section className="panel chartPanel">
      <div className="sectionHeader">
        <h2>Price Chart</h2>
        <span className="pill neutral">{range}</span>
      </div>
      <ResponsiveContainer width="100%" height={330}>
        <LineChart data={data}>
          <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
          <XAxis dataKey="date" minTickGap={36} stroke="#91a3b8" />
          <YAxis stroke="#91a3b8" domain={["auto", "auto"]} />
          <Tooltip contentStyle={{ background: "#101820", border: "1px solid #2a394a" }} />
          <Line type="monotone" dataKey="close" stroke="#67e8f9" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
