from __future__ import annotations

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator
from ta.volatility import AverageTrueRange, BollingerBands


FEATURE_COLUMNS = [
    "SMA_20",
    "SMA_50",
    "SMA_200",
    "EMA_20",
    "EMA_50",
    "RSI",
    "MACD",
    "MACD_signal",
    "MACD_hist",
    "BB_upper",
    "BB_lower",
    "BB_middle",
    "ATR",
    "Daily_Return",
    "Return_5D",
    "Return_10D",
    "Return_20D",
    "Volume_MA_20",
    "Volume_Ratio",
    "Rolling_Volatility",
]


def add_indicators_for_symbol(group: pd.DataFrame) -> pd.DataFrame:
    frame = group.sort_values("Date").copy()
    close = frame["Close"]
    high = frame["High"]
    low = frame["Low"]
    volume = frame["Volume"]

    frame["SMA_20"] = SMAIndicator(close, window=20).sma_indicator()
    frame["SMA_50"] = SMAIndicator(close, window=50).sma_indicator()
    frame["SMA_200"] = SMAIndicator(close, window=200).sma_indicator()
    frame["EMA_20"] = EMAIndicator(close, window=20).ema_indicator()
    frame["EMA_50"] = EMAIndicator(close, window=50).ema_indicator()
    frame["RSI"] = RSIIndicator(close, window=14).rsi()

    macd = MACD(close)
    frame["MACD"] = macd.macd()
    frame["MACD_signal"] = macd.macd_signal()
    frame["MACD_hist"] = macd.macd_diff()

    bands = BollingerBands(close, window=20)
    frame["BB_upper"] = bands.bollinger_hband()
    frame["BB_lower"] = bands.bollinger_lband()
    frame["BB_middle"] = bands.bollinger_mavg()
    frame["ATR"] = AverageTrueRange(high, low, close, window=14).average_true_range()

    frame["Daily_Return"] = close.pct_change()
    frame["Return_5D"] = close.pct_change(5)
    frame["Return_10D"] = close.pct_change(10)
    frame["Return_20D"] = close.pct_change(20)
    frame["Volume_MA_20"] = volume.rolling(20).mean()
    frame["Volume_Ratio"] = volume / frame["Volume_MA_20"]
    frame["Rolling_Volatility"] = frame["Daily_Return"].rolling(20).std()
    return frame


def create_features(df: pd.DataFrame, dropna: bool = True) -> pd.DataFrame:
    featured = pd.concat(
        [add_indicators_for_symbol(group) for _, group in df.groupby("Symbol")],
        ignore_index=True,
    )
    featured["Target"] = (
        featured.groupby("Symbol")["Close"].shift(-1) > featured["Close"]
    ).astype("float")
    featured.loc[featured.groupby("Symbol").tail(1).index, "Target"] = np.nan
    featured.replace([np.inf, -np.inf], np.nan, inplace=True)
    if dropna:
        featured.dropna(subset=FEATURE_COLUMNS + ["Target"], inplace=True)
    featured.sort_values(["Date", "Symbol"], inplace=True)
    featured.reset_index(drop=True, inplace=True)
    return featured
