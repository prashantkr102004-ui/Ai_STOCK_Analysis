import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import (
    routes_backtest,
    routes_data,
    routes_fundamentals,
    routes_health,
    routes_predictions,
    routes_sentiment,
    routes_stocks,
)
from backend.app.core.config import get_settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI MarketGuard API",
    description="AI-powered stock market intelligence and historical prediction platform.",
    version="0.1.0",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router, prefix="/api")
app.include_router(routes_data.router, prefix="/api")
app.include_router(routes_stocks.router, prefix="/api")
app.include_router(routes_predictions.router, prefix="/api")
app.include_router(routes_backtest.router, prefix="/api")
app.include_router(routes_sentiment.router, prefix="/api")
app.include_router(routes_fundamentals.router, prefix="/api")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
