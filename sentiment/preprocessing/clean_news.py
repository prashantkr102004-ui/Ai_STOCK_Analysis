from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"date", "headline"}
OPTIONAL_COLUMNS = {"symbol", "article"}


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_symbol(value: object) -> str | None:
    symbol = clean_text(value).upper()
    if not symbol:
        return None
    if not symbol.replace("-", "").isalnum():
        return None
    return symbol


def load_news_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    frame = pd.read_csv(path)
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"News CSV missing required columns: {', '.join(sorted(missing))}")

    loaded = len(frame)
    for column in OPTIONAL_COLUMNS - set(frame.columns):
        frame[column] = None

    frame["headline"] = frame["headline"].map(clean_text)
    frame["article"] = frame["article"].map(clean_text)
    frame["symbol"] = frame["symbol"].map(normalize_symbol)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["text"] = (frame["headline"] + " " + frame["article"]).map(clean_text)

    valid = frame.dropna(subset=["date"]).copy()
    valid = valid[(valid["headline"] != "") & (valid["text"] != "")]
    valid = valid.drop_duplicates(subset=["date", "symbol", "headline", "article"])
    valid["date"] = valid["date"].dt.strftime("%Y-%m-%d")
    retained = len(valid)
    logger.info("Loaded news records=%s removed=%s retained=%s path=%s", loaded, loaded - retained, retained, path)

    return valid[["date", "symbol", "headline", "article", "text"]].reset_index(drop=True)


def load_news_folder(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    files = sorted(path.glob("*.csv"))
    if not files:
        return pd.DataFrame(columns=["date", "symbol", "headline", "article", "text"])

    frames = [load_news_csv(file) for file in files]
    combined = pd.concat(frames, ignore_index=True)
    loaded = len(combined)
    combined = combined.drop_duplicates(subset=["date", "symbol", "headline", "article"]).reset_index(drop=True)
    logger.info("Combined news records=%s removed=%s retained=%s", loaded, loaded - len(combined), len(combined))
    return combined
