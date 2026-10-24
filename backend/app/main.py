from pathlib import Path
from dotenv import load_dotenv

# Load the repo-root .env BEFORE importing services, whose module-level
# os.getenv(...) calls would otherwise miss it. main.py lives in backend/app/,
# so parents[2] is the project root.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .services import fetch_elexon_data, process_and_align_data, calculate_metrics
from .models import DataResponse, MetricsResponse, WindDataPoint
import pandas as pd
import os
import logging
from datetime import datetime, date
logger = logging.getLogger(__name__)

app = FastAPI(title="UK Wind Power Analytics API")

_allowed = os.getenv("ALLOWED_ORIGINS", "*")
_origins = ["*"] if _allowed.strip() == "*" else [o.strip() for o in _allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET"],          # this API is read-only; tighten from "*"
    allow_headers=["*"],
)

def _num(v):
    """Coerce a pandas scalar to a JSON-safe float, or None for NaN/None."""
    return None if pd.isna(v) else float(v)

@app.get("/health", tags=["system"])
def health():
    """Liveness probe for orchestrators / PaaS health checks."""
    return {"status": "ok"}

_JAN_2026_START = date(2026, 1, 1)
_JAN_2026_END   = date(2026, 1, 31)

@app.get(
    "/api/wind-data",
    response_model=DataResponse,
    description=(
        "Aligned 30-minute actual (FUELHH, fuelType=WIND) vs day-ahead forecast "
        "(WINDFOR) series plus MAE/RMSE/bias for one date. "
        "Only 2026-01-01..2026-01-31 are accepted; any other date returns 400."
    ),
)
def get_wind_data(date: str = Query(..., description="Date in YYYY-MM-DD format, restricted to January 2026")):
    # req 19: strict YYYY-MM-DD parse -> 400 on malformed input (client fault, not upstream)
    try:
        d = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    # req 5: enforce January 2026 window -> 400 outside it
    if d < _JAN_2026_START or d > _JAN_2026_END:
        raise HTTPException(
            status_code=400,
            detail="Date out of range. Only January 2026 (2026-01-01..2026-01-31) is supported.",
        )

    # req 15: upstream fetch/process; surface failures as 503, never mask with fake data
    try:
        df_actual, df_forecast = fetch_elexon_data(date, date)
        df_merged = process_and_align_data(df_actual, df_forecast, date)
    except Exception:
        logger.exception("Elexon fetch/process failed for %s", date)
        raise HTTPException(status_code=503, detail="Upstream data source unavailable.")

    if df_merged.empty:
        return DataResponse(data=[], metrics=MetricsResponse(mae=0, rmse=0, bias=0, dataPoints=0))

    metrics = calculate_metrics(df_merged)

    data_points = [
        WindDataPoint(
            startTime=row['startTime'],
            actualGeneration=_num(row.get('generation_actual')),
            forecastGeneration=_num(row.get('generation_forecast'))
        ) for _, row in df_merged.iterrows()
    ]

    return DataResponse(data=data_points, metrics=MetricsResponse(**metrics))