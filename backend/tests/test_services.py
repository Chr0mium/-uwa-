import pandas as pd
from app.services import calculate_metrics, process_and_align_data


def test_calculate_metrics_perfect_forecast():
    df = pd.DataFrame({
        'generation_actual': [100, 200, 300],
        'generation_forecast': [100, 200, 300],
    })
    metrics = calculate_metrics(df)
    assert metrics['mae'] == 0
    assert metrics['rmse'] == 0
    assert metrics['bias'] == 0
    assert metrics['dataPoints'] == 3


def test_calculate_metrics_with_bias():
    df = pd.DataFrame({
        'generation_actual': [100, 200],
        'generation_forecast': [110, 210],  # constant +10 offset
    })
    metrics = calculate_metrics(df)
    assert metrics['mae'] == 10
    assert metrics['rmse'] == 10   # closes the false-pass hole: verifies sqrt on non-zero diff
    assert metrics['bias'] == 10
    assert metrics['dataPoints'] == 2


def test_process_and_align_data_respects_day_ahead_cutoff():
    # req 9: a forecast published AFTER the day-ahead cutoff (start of target
    # day) must be dropped; among pre-cutoff revisions the latest wins. Also
    # proves the 1:1 merge (#8): slot 00:00 had TWO forecast rows and must
    # collapse to ONE, so len(merged) tracks the actual grid, not the raw rows.
    actual = pd.DataFrame({
        'startTime': ['2026-01-15 00:00', '2026-01-15 00:30'],
        'generation': [100.0, 200.0],
    })
    forecast = pd.DataFrame({
        'startTime': [
            '2026-01-15 00:00',  # two day-ahead revisions for slot 00:00
            '2026-01-15 00:00',
            '2026-01-15 00:30',  # published 06:00 on the delivery day = NOT day-ahead
        ],
        'publishTime': [
            '2026-01-14 08:00',  # pre-cutoff, older  -> should lose to the 16:00 row
            '2026-01-14 16:00',  # pre-cutoff, latest -> should win (keep="last")
            '2026-01-15 06:00',  # POST-cutoff        -> must be dropped entirely
        ],
        'generation': [50.0, 110.0, 999.0],
    })

    merged = process_and_align_data(actual, forecast, '2026-01-15')

    assert len(merged) == 2  # both actual slots survive via left join; no row explosion
    slot00 = merged[merged['startTime'] == pd.Timestamp('2026-01-15 00:00:00')]
    slot30 = merged[merged['startTime'] == pd.Timestamp('2026-01-15 00:30:00')]
    assert slot00['generation_forecast'].iloc[0] == 110.0      # latest pre-cutoff revision
    assert pd.isna(slot30['generation_forecast'].iloc[0])      # its only forecast was post-cutoff -> nulled
    assert (merged['generation_forecast'] == 999.0).sum() == 0  # hindsight value never leaks


def test_process_and_align_handles_missing_and_invalid_data():
    # req 14: unparseable startTime dropped; non-numeric / NaN forecast nulled and
    # excluded from metrics; numeric-as-string coerced to a valid value.
    actual = pd.DataFrame({
        'startTime': ['2026-01-15 00:00', '2026-01-15 00:30', '2026-01-15 01:00', 'not-a-date'],
        'generation': [100, 200, 300, 400],
    })
    forecast = pd.DataFrame({
        'startTime': ['2026-01-15 00:00', '2026-01-15 00:30', '2026-01-15 01:00'],
        'publishTime': ['2026-01-14 16:00', '2026-01-14 16:00', '2026-01-14 16:00'],
        'generation': ['110', float('nan'), 'abc'],  # coerce-ok, NaN, non-numeric
    })

    merged = process_and_align_data(actual, forecast, '2026-01-15')
    metrics = calculate_metrics(merged)

    assert len(merged) == 3                                   # 'not-a-date' row dropped (NaT)
    assert metrics['dataPoints'] == 1                         # only the coerced 00:00 pair is valid
    assert metrics['mae'] == 10.0 and metrics['rmse'] == 10.0 and metrics['bias'] == 10.0
    assert pd.isna(merged.loc[merged['startTime'] == pd.Timestamp('2026-01-15 00:30:00'), 'generation_forecast'].iloc[0])
    assert pd.isna(merged.loc[merged['startTime'] == pd.Timestamp('2026-01-15 01:00:00'), 'generation_forecast'].iloc[0])