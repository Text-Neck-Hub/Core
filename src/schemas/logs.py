from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Log(BaseModel):
    angle: float
    shoulder_y_diff: float
    shoulder_y_avg: float
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
