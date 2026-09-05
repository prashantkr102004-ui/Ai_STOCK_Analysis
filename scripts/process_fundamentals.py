from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.fundamental_service import process_fundamentals


def main() -> int:
    result = process_fundamentals()
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
