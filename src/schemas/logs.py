from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Log(BaseModel):
    angle: float
    shoulder_y_diff: float
    shoulder_y_avg: float
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
