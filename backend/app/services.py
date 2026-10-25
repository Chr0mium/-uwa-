import pandas as pd
import httpx
import os
from .mock_data import generate_mock_jan_2026


def _to_naive_utc(s):
    """Parse to UTC then strip tz -> naive-UTC wall clock. No-op on already-naive
    (mock/test) input; converts live 'Z'/offset stamps to the same naive-UTC basis
    so the cutoff compare (#9) and the startTime merge key (#8) are tz-consistent.
    Fixes the live-only 'tz-aware vs naive' TypeError. Bad values -> NaT (#14)."""
    return pd.to_datetime(s, errors="coerce", utc=True).dt.tz_localize(None)


USE_MOCK = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
_PAGE_SIZE = 1000


def _iso_midnight(ts: pd.Timestamp) -> str:
    """Half-open window bound as full ISO-8601 UTC ('YYYY-MM-DDT00:00:00Z').
    Bare 'YYYY-MM-DD' was IGNORED by the live endpoint (probe returned today's rows
    for a Jan request), so we send the documented v1 datetime form."""
    return ts.strftime("%Y-%m-%dT00:00:00Z")


def _get_paginated(client, url, params):
    """req 7/9: follow links.next so WINDFOR (many publications/slot) is not
    truncated to one page. (Live probe saw links=None, so this is one page in
    practice, but the loop stays correct if Elexon ever paginates.)"""
    rows, next_url, next_params = [], url, params
    while next_url:
        r = client.get(next_url, params=next_params, timeout=15.0)
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValueError("Unexpected Elexon response shape: missing 'data' list")
        rows.extend(data)
        nxt = (payload.get("links") or {}).get("next")
        next_url, next_params = (nxt, None) if nxt else (None, None)
    return rows




def fetch_elexon_data(start_date: str, end_date: str):
    if USE_MOCK:
        return generate_mock_jan_2026()

    d_start = pd.Timestamp(start_date).date()
    d_end = pd.Timestamp(end_date).date()

    with httpx.Client(
        headers={"Accept": "application/json"},
        timeout=60.0,
    ) as client:
        # Actual wind generation for the requested settlement dates.
        actual_response = client.get(
            f"{_BASE}/datasets/FUELHH",
            params={
                "settlementDateFrom": d_start.isoformat(),
                "settlementDateTo": d_end.isoformat(),
                "fuelType": "WIND",
            },
        )
        actual_response.raise_for_status()
        actual_payload = actual_response.json()
        actual_rows = (
            actual_payload
            if isinstance(actual_payload, list)
            else actual_payload.get("data", [])
        )

        # Latest historical forecast publication available before the
        # delivery date starts.
        forecast_cutoff = pd.Timestamp(d_start).strftime(
            "%Y-%m-%dT00:00:00Z"
        )
        forecast_response = client.get(
            f"{_BASE}/forecast/generation/wind/history",
            params={"publishTime": forecast_cutoff},
        )
        forecast_response.raise_for_status()
        forecast_payload = forecast_response.json()
        forecast_rows = (
            forecast_payload
            if isinstance(forecast_payload, list)
            else forecast_payload.get("data", [])
        )

    df_actual = pd.DataFrame(actual_rows)
    if df_actual.empty:
        df_actual = pd.DataFrame(columns=["startTime", "generation"])
    elif not {"startTime", "generation"}.issubset(df_actual.columns):
        raise ValueError("FUELHH response missing required fields")

    if "fuelType" in df_actual.columns:
        df_actual = df_actual[df_actual["fuelType"] == "WIND"]

    df_forecast = pd.DataFrame(forecast_rows)
    if df_forecast.empty:
        df_forecast = pd.DataFrame(
            columns=["startTime", "publishTime", "generation"]
        )
    elif not {"startTime", "publishTime", "generation"}.issubset(
        df_forecast.columns
    ):
        raise ValueError("Historical WINDFOR response missing required fields")

    return df_actual, df_forecast

def process_and_align_data(
    df_actual: pd.DataFrame,
    df_forecast: pd.DataFrame,
    target_date: str,
):
    target = pd.to_datetime(target_date).date()
    cutoff = pd.Timestamp(target)

    # Actual generation: retain the original 30-minute intervals.
    a = df_actual.copy()
    a["startTime"] = _to_naive_utc(a["startTime"])
    a["generation"] = pd.to_numeric(a["generation"], errors="coerce")
    a = a[a["startTime"].dt.date == target].copy()

    if not df_actual.empty and a.empty:
        raise ValueError(
            "Elexon returned actual data but no rows on the target date."
        )

    a = a.dropna(subset=["startTime"])
    a = a.rename(columns={"generation": "generation_actual"})

    # Forecasts: retain only publications available before the delivery day.
    f = df_forecast.copy()
    f["startTime"] = _to_naive_utc(f["startTime"])
    f["publishTime"] = _to_naive_utc(f["publishTime"])
    f["generation"] = pd.to_numeric(f["generation"], errors="coerce")

    f = f[
        (f["startTime"].dt.date == target)
        & (f["publishTime"] <= cutoff)
    ].copy()

    # Keep the latest eligible revision for each hourly forecast.
    f = (
        f.dropna(subset=["startTime", "publishTime"])
        .sort_values("publishTime")
        .drop_duplicates(subset=["startTime"], keep="last")
    )

    # Keep the latest eligible publication for each exact timestamp.
    f = (
        f.sort_values("publishTime")
        .drop_duplicates(subset=["startTime"], keep="last")
    )

    a = a.rename(columns={"generation": "generation_actual"})
    f = f.rename(columns={"generation": "generation_forecast"})

    # Exact timestamp matching only; never copy hourly values into
    # half-hour intervals or use forecasts published after the cutoff.
    merged = pd.merge(
        a,
        f[["startTime", "generation_forecast"]],
        on="startTime",
        how="left",
        validate="one_to_one",
    )

    return merged.dropna(subset=["startTime"])

def calculate_metrics(df: pd.DataFrame):
    valid = df.dropna(subset=["generation_actual", "generation_forecast"])
    if valid.empty:
                return {"mae": 0, "rmse": 0, "bias": 0, "dataPoints": 0}
    actual = valid["generation_actual"]
    forecast = valid["generation_forecast"]
    mae = (actual - forecast).abs().mean()
    rmse = ((actual - forecast) ** 2).mean() ** 0.5
    bias = (forecast - actual).mean()
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "bias": round(bias, 2), "dataPoints": len(valid)}