const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, value);
    }
  });
  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}

export const api = {
  getHealth: () => request("/health"),
  getStocks: () => request("/stocks"),
  getStock: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}`),
  getHistory: (symbol, params) => request(`/stocks/${encodeURIComponent(symbol)}/history${query(params)}`),
  getIndicators: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/indicators`),
  getPrediction: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/prediction`),
  getSignal: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/signal`),
  getExplanation: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/explanation`),
  getNews: (symbol, params) => request(`/stocks/${encodeURIComponent(symbol)}/news${query(params)}`),
  getSentiment: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/sentiment`),
  getSentimentHistory: (symbol, params) => request(`/stocks/${encodeURIComponent(symbol)}/sentiment/history${query(params)}`),
  getFundamentals: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/fundamentals`),
  getFundamentalsHistory: (symbol, params) => request(`/stocks/${encodeURIComponent(symbol)}/fundamentals/history${query(params)}`),
  runBacktest: (symbol, payload) =>
    request(`/stocks/${encodeURIComponent(symbol)}/backtest`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  getBacktest: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/backtest`),
  getBacktestEquity: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/backtest/equity`),
  getBacktestTrades: (symbol) => request(`/stocks/${encodeURIComponent(symbol)}/backtest/trades`),
  getModelStatus: () => request("/model/status"),
  getModelComparison: () => request("/model/comparison"),
  getFeatureImportance: () => request("/model/feature-importance"),
  getDataStatus: () => request("/data/status")
};
