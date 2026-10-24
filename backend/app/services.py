import pandas as pd
import httpx
import os
from .mock_data import generate_mock_jan_2026

# req 18/5/23: mock is an OPT-IN dev/demo mode only. Default FALSE so a
# production deploy serves real Elexon data or errors — never silent fakes.
USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

_BASE = "https://data.elexon.co.uk/bmrs/api/v1"


def _get_paginated(client, url, params):
    """req 7/9: follow links.next so WINDFOR (many publications/slot) is not
    truncated to one page, which would silently drop the day-ahead rows."""
    rows, next_url, next_params = [], url, params
    while next_url:
        r = client.get(next_url, params=next_params, timeout=15.0)   # req 15: no hang
        r.raise_for_status()                                        # req 15: 4xx/5xx -> raise -> 503
        payload = r.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValueError("Unexpected Elexon response shape: missing 'data' list")
        rows.extend(data)
        nxt = (payload.get("links") or {}).get("next")
        next_url, next_params = (nxt, None) if nxt else (None, None)  # next is absolute URL
    return rows


def fetch_elexon_data(start_date: str, end_date: str):
    if USE_MOCK:
        return generate_mock_jan_2026()

    # req 9 (defensive): widen the WINDFOR window by one day so the day-ahead
    # publications (publishTime on the prior evening) are present whether the
    # endpoint filters from/to on startTime OR on publishTime. Extra rows are
    # discarded downstream by the startTime==target filter; cost is one page.
    _wind_from = (pd.Timestamp(start_date) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    with httpx.Client(headers={"Accept": "application/json"}) as client:
        fuel_rows = _get_paginated(                       # req 6: FUELHH, WIND only
            client, f"{_BASE}/datasets/FUELHH",
            {"from": start_date, "to": end_date, "fuelType": "WIND"},
        )
        wind_rows = _get_paginated(                       # req 7 + req 9 window
            client, f"{_BASE}/datasets/WINDFOR",
            {"from": _wind_from, "to": end_date},
        )

    df_actual = pd.DataFrame(fuel_rows)
    if df_actual.empty:
        df_actual = pd.DataFrame(columns=["startTime", "generation"])
    else:
        if not {"startTime", "generation"}.issubset(df_actual.columns):
            raise ValueError("FUELHH response missing required fields")
        if "fuelType" in df_actual.columns:               # req 6: belt-and-braces client filter
            df_actual = df_actual[df_actual["fuelType"] == "WIND"]

    df_forecast = pd.DataFrame(wind_rows)
    if df_forecast.empty:
        df_forecast = pd.DataFrame(columns=["startTime", "publishTime", "generation"])
    elif not {"startTime", "publishTime", "generation"}.issubset(df_forecast.columns):
        raise ValueError("WINDFOR response missing required fields")

    return df_actual, df_forecast


def process_and_align_data(df_actual: pd.DataFrame, df_forecast: pd.DataFrame, target_date: str):
    target = pd.to_datetime(target_date).date()
    cutoff = pd.Timestamp(target)                         # req 9: day-ahead boundary = start of target day

    a = df_actual.copy()
    a["startTime"] = pd.to_datetime(a["startTime"], errors="coerce")     # req 14: bad ts -> NaT -> dropped
    a["generation"] = pd.to_numeric(a["generation"], errors="coerce")    # req 14: bad value -> NaN
    a = a[a["startTime"].dt.date == target]               # req 5/8: scope to the one delivery day

    f = df_forecast.copy()
    f["startTime"] = pd.to_datetime(f["startTime"], errors="coerce")     # req 14
    f["publishTime"] = pd.to_datetime(f["publishTime"], errors="coerce") # req 14
    f["generation"] = pd.to_numeric(f["generation"], errors="coerce")    # req 14
    f = f[f["startTime"].dt.date == target]               # req 5/8
    f = f[f["publishTime"] <= cutoff]                     # req 9: only forecasts published by the day-ahead decision time (NaT publishTime fails this compare -> dropped, req 14)
    f = f.sort_values("publishTime").drop_duplicates(subset=["startTime"], keep="last")  # req 8/9: one row per slot -> 1:1 merge, no explosion

    merged = pd.merge(a, f, on="startTime", how="left", suffixes=("_actual", "_forecast"))  # req 8: 30-min grid
    merged = merged.dropna(subset=["startTime"])          # req 14
    return merged


def calculate_metrics(df: pd.DataFrame):                  # req 13/14 — unchanged, correct
    valid = df.dropna(subset=["generation_actual", "generation_forecast"])
    if valid.empty:
        return {"mae": 0, "rmse": 0, "bias": 0, "dataPoints": 0}
    actual = valid["generation_actual"]
    forecast = valid["generation_forecast"]
    mae = (actual - forecast).abs().mean()
    rmse = ((actual - forecast) ** 2).mean() ** 0.5
    bias = (forecast - actual).mean()
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "bias": round(bias, 2), "dataPoints": len(valid)}