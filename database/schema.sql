CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    date DATE NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    UNIQUE(stock_id, date)
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    prediction_date DATE NOT NULL,
    prediction VARCHAR(8) NOT NULL,
    probability_up DOUBLE PRECISION NOT NULL,
    probability_down DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    UNIQUE(stock_id, prediction_date, model_version)
);

CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DOUBLE PRECISION NOT NULL,
    final_capital DOUBLE PRECISION NOT NULL,
    total_return DOUBLE PRECISION NOT NULL,
    win_rate DOUBLE PRECISION NOT NULL,
    max_drawdown DOUBLE PRECISION NOT NULL,
    sharpe_ratio DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) UNIQUE NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    training_date DATE NOT NULL,
    accuracy DOUBLE PRECISION,
    precision DOUBLE PRECISION,
    recall DOUBLE PRECISION,
    f1 DOUBLE PRECISION,
    roc_auc DOUBLE PRECISION,
    model_path VARCHAR(500) NOT NULL
);
