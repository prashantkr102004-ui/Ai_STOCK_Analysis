from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.sentiment_service import process_news_sentiment
from sentiment.finbert import SentimentModelUnavailable


def main() -> int:
    try:
        result = process_news_sentiment(use_model=True)
    except SentimentModelUnavailable as exc:
        print(str(exc))
        print("Install optional packages with: python -m pip install transformers torch")
        print("Then rerun: python scripts/process_news_sentiment.py")
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
