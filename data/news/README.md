# Local Historical News Data

Place historical financial-news CSV files in this folder.

Supported columns:

- `date` - required, parseable date
- `headline` - required, non-empty text
- `article` - optional longer text
- `symbol` - optional stock symbol

Rows without `symbol` are treated as general-market news. The system does not invent symbol mappings.

`sample_financial_news.csv` is synthetic sample data for tests and local development only.
