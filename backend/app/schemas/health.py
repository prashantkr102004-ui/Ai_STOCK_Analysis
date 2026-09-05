from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    backend: str | None = None
    database: str | None = None
    model: str | None = None
    data: str | None = None
