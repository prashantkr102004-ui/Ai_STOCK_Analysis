from pydantic import BaseModel


class DataStatusResponse(BaseModel):
    number_of_stocks: int
    total_historical_records: int
    earliest_available_date: str
    latest_available_date: str
    number_of_processed_files: int
    last_processing_time: str | None = None
