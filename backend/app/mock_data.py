import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_jan_2026():
    start = datetime(2026, 1, 1)
    end = datetime(2026, 1, 31, 23, 30)
    dates = pd.date_range(start, end, freq='30min')
    
    # Simulate wind generation (base + noise + daily pattern)
    actual = 2000 + 1500 * np.sin(np.arange(len(dates)) * 2 * np.pi / 48) + np.random.normal(0, 300, len(dates))
    actual = np.clip(actual, 0, 5000)
    
    # Simulate forecasts (published day ahead with some error)
    forecast = actual + np.random.normal(100, 400, len(dates)) 
    forecast = np.clip(forecast, 0, 5000)
    
    df_actual = pd.DataFrame({'startTime': dates, 'generation': actual})
    df_forecast = pd.DataFrame({
        'startTime': dates, 
        'publishTime': dates - timedelta(days=1), # Day ahead
        'generation': forecast
    })
    return df_actual, df_forecast