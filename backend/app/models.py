from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class WindDataPoint(BaseModel):
    startTime: datetime
    actualGeneration: Optional[float] = None
    forecastGeneration: Optional[float] = None

class MetricsResponse(BaseModel):
    mae: float = Field(description="Mean Absolute Error")
    rmse: float = Field(description="Root Mean Square Error")
    bias: float = Field(description="Forecast Bias (Forecast - Actual)")
    dataPoints: int

class DataResponse(BaseModel):
    data: List[WindDataPoint]
    metrics: MetricsResponse