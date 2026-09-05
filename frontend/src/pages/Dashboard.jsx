import React, { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import StockSearch from "../components/StockSearch.jsx";
import MetricCard from "../components/MetricCard.jsx";
import StockChart from "../components/StockChart.jsx";
import PredictionCard from "../components/PredictionCard.jsx";
import SignalCard from "../components/SignalCard.jsx";
import IndicatorsGrid from "../components/IndicatorsGrid.jsx";
import BacktestForm from "../components/BacktestForm.jsx";
import BacktestCard from "../components/BacktestCard.jsx";
import EquityCurveChart from "../components/EquityCurveChart.jsx";
import TradeTable from "../components/TradeTable.jsx";
import ModelStatus from "../components/ModelStatus.jsx";
import FeatureImportance from "../components/FeatureImportance.jsx";
import DataStatus from "../components/DataStatus.jsx";
import NewsSentiment from "../components/NewsSentiment.jsx";
import Fundamentals from "../components/Fundamentals.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import { api } from "../services/api.js";
import { formatCurrency, formatDate, formatNumber } from "../utils/formatters.js";

const RANGE_OPTIONS = [
  ["1M", 22],
  ["3M", 66],
  ["6M", 132],
  ["1Y", 252],
  ["ALL", null]
];

const initialBacktestForm = {
  start_date: "",
  end_date: "",
  initial_capital: "100000",
  transaction_cost: "0.001",
  slippage: "0"
};

function messageFrom(error, fallback) {
  return error?.message || fallback;
}

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState("");
  const [range, setRange] = useState("1Y");

  const [detail, setDetail] = useState(null);
  const [history, setHistory] = useState([]);
  const [indicators, setIndicators] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [signal, setSignal] = useState(null);
  const [sentiment, setSentiment] = useState(null);
  const [sentimentHistory, setSentimentHistory] = useState([]);
  const [news, setNews] = useState([]);
  const [fundamentals, setFundamentals] = useState(null);
  const [fundamentalsHistory, setFundamentalsHistory] = useState([]);
  const [backtest, setBacktest] = useState(null);
  const [equity, setEquity] = useState([]);
  const [trades, setTrades] = useState([]);
  const [model, setModel] = useState(null);
  const [featureImportance, setFeatureImportance] = useState([]);
  const [dataStatus, setDataStatus] = useState(null);

  const [globalLoading, setGlobalLoading] = useState(true);
  const [stockLoading, setStockLoading] = useState(false);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [form, setForm] = useState(initialBacktestForm);
  const [formError, setFormError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadGlobal() {
      setGlobalLoading(true);
      const nextErrors = {};
      const [healthResult, stocksResult, modelResult, featuresResult, statusResult] = await Promise.allSettled([
        api.getHealth(),
        api.getStocks(),
        api.getModelStatus(),
        api.getFeatureImportance(),
        api.getDataStatus()
      ]);

      if (!mounted) return;

      if (healthResult.status === "fulfilled") setHealth(healthResult.value);
      else {
        setHealth({ status: "offline" });
        nextErrors.health = "Backend unavailable.";
      }

      if (stocksResult.status === "fulfilled") {
        setStocks(stocksResult.value);
        setSelected(stocksResult.value[0]?.symbol || "");
      } else {
        nextErrors.stocks = messageFrom(stocksResult.reason, "Unable to load stocks.");
      }

      if (modelResult.status === "fulfilled") setModel(modelResult.value);
      else nextErrors.model = messageFrom(modelResult.reason, "Unable to load model status.");

      if (featuresResult.status === "fulfilled") setFeatureImportance(featuresResult.value);
      else nextErrors.features = messageFrom(featuresResult.reason, "Unable to load feature importance.");

      if (statusResult.status === "fulfilled") setDataStatus(statusResult.value);
      else nextErrors.data = messageFrom(statusResult.reason, "Unable to load dataset status.");

      setErrors(nextErrors);
      setGlobalLoading(false);
    }

    loadGlobal();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let mounted = true;

    async function loadStock() {
      setStockLoading(true);
      setErrors((current) => ({
        ...current,
        detail: "",
        history: "",
        indicators: "",
        prediction: "",
        signal: "",
        sentiment: "",
        sentimentHistory: "",
        news: "",
        fundamentals: "",
        fundamentalsHistory: "",
        backtest: "",
        equity: "",
        trades: ""
      }));
      setDetail(null);
      setHistory([]);
      setIndicators(null);
      setPrediction(null);
      setSignal(null);
      setSentiment(null);
      setSentimentHistory([]);
      setNews([]);
      setFundamentals(null);
      setFundamentalsHistory([]);
      setBacktest(null);
      setEquity([]);
      setTrades([]);

      const nextErrors = {};
      const [
        detailResult,
        historyResult,
        indicatorsResult,
        predictionResult,
        signalResult,
        sentimentResult,
        sentimentHistoryResult,
        newsResult,
        fundamentalsResult,
        fundamentalsHistoryResult,
        backtestResult,
        equityResult,
        tradesResult
      ] =
        await Promise.allSettled([
          api.getStock(selected),
          api.getHistory(selected, { limit: 5000 }),
          api.getIndicators(selected),
          api.getPrediction(selected),
          api.getExplanation(selected),
          api.getSentiment(selected),
          api.getSentimentHistory(selected, { limit: 250 }),
          api.getNews(selected, { limit: 20 }),
          api.getFundamentals(selected),
          api.getFundamentalsHistory(selected),
          api.getBacktest(selected),
          api.getBacktestEquity(selected),
          api.getBacktestTrades(selected)
        ]);

      if (!mounted) return;

      if (detailResult.status === "fulfilled") {
        setDetail(detailResult.value);
        setForm((current) => ({
          ...current,
          start_date: detailResult.value.start_date,
          end_date: detailResult.value.end_date
        }));
      } else nextErrors.detail = messageFrom(detailResult.reason, "Stock details unavailable.");

      if (historyResult.status === "fulfilled") setHistory(historyResult.value.history);
      else nextErrors.history = messageFrom(historyResult.reason, "Historical data unavailable.");

      if (indicatorsResult.status === "fulfilled") setIndicators(indicatorsResult.value);
      else nextErrors.indicators = messageFrom(indicatorsResult.reason, "Indicators unavailable.");

      if (predictionResult.status === "fulfilled") setPrediction(predictionResult.value);
      else nextErrors.prediction = messageFrom(predictionResult.reason, "Prediction unavailable.");

      if (signalResult.status === "fulfilled") setSignal(signalResult.value);
      else nextErrors.signal = messageFrom(signalResult.reason, "Signal unavailable.");

      if (sentimentResult.status === "fulfilled") setSentiment(sentimentResult.value);
      else nextErrors.sentiment = messageFrom(sentimentResult.reason, "No historical news sentiment available for this stock.");

      if (sentimentHistoryResult.status === "fulfilled") setSentimentHistory(sentimentHistoryResult.value);
      else nextErrors.sentimentHistory = messageFrom(sentimentHistoryResult.reason, "");

      if (newsResult.status === "fulfilled") setNews(newsResult.value);
      else nextErrors.news = messageFrom(newsResult.reason, "");

      if (fundamentalsResult.status === "fulfilled") setFundamentals(fundamentalsResult.value);
      else nextErrors.fundamentals = messageFrom(fundamentalsResult.reason, "No local fundamental data available for this stock.");

      if (fundamentalsHistoryResult.status === "fulfilled") setFundamentalsHistory(fundamentalsHistoryResult.value);
      else nextErrors.fundamentalsHistory = messageFrom(fundamentalsHistoryResult.reason, "");

      if (backtestResult.status === "fulfilled") setBacktest(backtestResult.value);
      else nextErrors.backtest = messageFrom(backtestResult.reason, "No saved backtest available.");

      if (equityResult.status === "fulfilled") setEquity(equityResult.value.equity_curve);
      else nextErrors.equity = messageFrom(equityResult.reason, "Equity curve unavailable.");

      if (tradesResult.status === "fulfilled") setTrades(tradesResult.value);
      else nextErrors.trades = messageFrom(tradesResult.reason, "Trade history unavailable.");

      setErrors((current) => ({
        ...current,
        detail: "",
        history: "",
        indicators: "",
        prediction: "",
        signal: "",
        sentiment: "",
        sentimentHistory: "",
        news: "",
        fundamentals: "",
        fundamentalsHistory: "",
        backtest: "",
        equity: "",
        trades: "",
        ...nextErrors
      }));
      setStockLoading(false);
    }

    loadStock();
    return () => {
      mounted = false;
    };
  }, [selected]);

  const filteredHistory = useMemo(() => {
    const days = RANGE_OPTIONS.find(([label]) => label === range)?.[1];
    if (!days) return history;
    return history.slice(-days);
  }, [history, range]);

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function validateBacktestForm() {
    const capital = Number(form.initial_capital);
    const cost = Number(form.transaction_cost);
    const slippage = Number(form.slippage);
    if (form.start_date && form.end_date && new Date(form.end_date) < new Date(form.start_date)) {
      return "End date must be greater than or equal to start date.";
    }
    if (!Number.isFinite(capital) || capital <= 0) return "Initial capital must be greater than zero.";
    if (!Number.isFinite(cost) || cost < 0) return "Transaction cost must be zero or greater.";
    if (!Number.isFinite(slippage) || slippage < 0) return "Slippage must be zero or greater.";
    return "";
  }

  async function submitBacktest(event) {
    event.preventDefault();
    const validation = validateBacktestForm();
    if (validation) {
      setFormError(validation);
      return;
    }

    setFormError("");
    setBacktestLoading(true);
    try {
      const payload = {
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        initial_capital: Number(form.initial_capital),
        transaction_cost: Number(form.transaction_cost),
        slippage: Number(form.slippage)
      };
      const result = await api.runBacktest(selected, payload);
      const [equityResult, tradesResult] = await Promise.all([
        api.getBacktestEquity(selected),
        api.getBacktestTrades(selected)
      ]);
      setBacktest(result);
      setEquity(equityResult.equity_curve);
      setTrades(tradesResult);
      setErrors((current) => ({ ...current, backtest: "", equity: "", trades: "" }));
    } catch (error) {
      setFormError(messageFrom(error, "Backtest failed."));
    } finally {
      setBacktestLoading(false);
    }
  }

  if (globalLoading && !stocks.length) {
    return (
      <main>
        <Navbar health={health} />
        <Loading label="Loading stocks, model status, and dataset information..." />
      </main>
    );
  }

  return (
    <main>
      <Navbar health={health} />
      <ErrorMessage message={errors.health || errors.stocks} />

      <section className="toolbar">
        <StockSearch stocks={stocks} selected={selected} onSelect={setSelected} search={search} onSearch={setSearch} />
        <div className="rangeGroup" aria-label="Chart range">
          {RANGE_OPTIONS.map(([label]) => (
            <button key={label} type="button" className={range === label ? "active" : ""} onClick={() => setRange(label)}>
              {label}
            </button>
          ))}
        </div>
      </section>

      <section className="metrics">
        <MetricCard label="Stock Symbol" value={selected || "N/A"} />
        <MetricCard label="Latest Historical Close" value={formatCurrency(detail?.latest_close)} />
        <MetricCard label="Latest Available Date" value={formatDate(detail?.latest_date)} />
        <MetricCard label="Historical Records" value={formatNumber(detail?.record_count)} helper={`${formatDate(detail?.start_date)} to ${formatDate(detail?.end_date)}`} />
      </section>

      <StockChart data={filteredHistory} loading={stockLoading} error={errors.history} range={range} />

      <section className="grid">
        <PredictionCard prediction={prediction} loading={stockLoading} error={errors.prediction} />
        <SignalCard signal={signal} loading={stockLoading} error={errors.signal} />
        <NewsSentiment
          sentiment={sentiment}
          history={sentimentHistory}
          news={news}
          loading={stockLoading}
          error={errors.sentiment || errors.sentimentHistory || errors.news}
        />
        <Fundamentals
          fundamentals={fundamentals}
          history={fundamentalsHistory}
          loading={stockLoading}
          error={errors.fundamentals || errors.fundamentalsHistory}
        />
        <IndicatorsGrid indicators={indicators} loading={stockLoading} error={errors.indicators} />
        <BacktestForm form={form} onChange={updateForm} onSubmit={submitBacktest} running={backtestLoading} error={formError} />
        <BacktestCard backtest={backtest} loading={stockLoading || backtestLoading} error={errors.backtest} signal={signal} model={model} />
        <EquityCurveChart data={equity} loading={stockLoading || backtestLoading} error={errors.equity} />
        <TradeTable trades={trades} loading={stockLoading || backtestLoading} error={errors.trades} />
        <ModelStatus model={model} loading={globalLoading} error={errors.model} />
        <FeatureImportance features={signal?.top_model_features || featureImportance} loading={globalLoading} error={errors.features} />
        <DataStatus status={dataStatus} loading={globalLoading} error={errors.data} />
      </section>

      <footer className="disclaimer">
        AI MarketGuard is an educational and analytical project. Predictions and historical backtests do not guarantee future market performance and are not financial advice.
      </footer>
    </main>
  );
}
