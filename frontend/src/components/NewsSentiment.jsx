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
import { formatDate, formatNumber, formatPercent } from "../utils/formatters.js";

export default function NewsSentiment({ sentiment, history, news, loading, error }) {
  if (loading) return <section className="panel wide">Loading news sentiment...</section>;

  return (
    <section className="panel wide">
      <div className="sectionHeader">
        <h2>News Sentiment</h2>
        {sentiment && <span className={`pill ${sentiment.sentiment?.toLowerCase()}`}>{sentiment.sentiment}</span>}
      </div>
      {error && <p className="mutedPanel">{error}</p>}
      {!sentiment && !error && <p className="mutedPanel">No historical news sentiment available for this stock.</p>}
      {sentiment && (
        <>
          <div className="indicatorGrid">
            <div><span>Overall Sentiment</span><strong>{sentiment.sentiment}</strong></div>
            <div><span>Sentiment Score</span><strong>{formatNumber(sentiment.sentiment_score, { maximumFractionDigits: 2 })}</strong></div>
            <div><span>Confidence</span><strong>{formatPercent(sentiment.confidence, true)}</strong></div>
            <div><span>News Items</span><strong>{formatNumber(sentiment.news_count)}</strong></div>
            <div><span>Latest Sentiment Date</span><strong>{formatDate(sentiment.date)}</strong></div>
          </div>
          {history?.length > 0 && (
            <div className="sentimentChart">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={history}>
                  <CartesianGrid stroke="#203040" strokeDasharray="3 3" />
                  <XAxis dataKey="date" stroke="#91a3b8" minTickGap={24} />
                  <YAxis stroke="#91a3b8" domain={[-100, 100]} />
                  <Tooltip contentStyle={{ background: "#101922", border: "1px solid #263849" }} />
                  <Line type="monotone" dataKey="average_sentiment_score" name="Sentiment score" stroke="#fbbf24" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <h3>Recent Headlines</h3>
          {news?.length ? (
            <div className="headlineList">
              {news.slice(0, 8).map((item) => (
                <article key={`${item.date}-${item.headline}`}>
                  <div>
                    <span>{formatDate(item.date)}</span>
                    <span className={`pill ${item.sentiment?.toLowerCase()}`}>{item.sentiment}</span>
                    <span>{formatPercent(item.confidence, true)}</span>
                  </div>
                  <p>{item.headline}</p>
                </article>
              ))}
            </div>
          ) : (
            <p className="mutedPanel">No recent cached headlines for this stock.</p>
          )}
        </>
      )}
      <small>Sentiment is calculated from local historical news only. News on a future date is never used for earlier signals.</small>
    </section>
  );
}
