
from typing import Annotated
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timezone


class Log(Document):
    user_id: Annotated[int, Indexed()]
    angle: float
    shoulder_y_diff: float
    shoulder_y_avg: float
    logged_at: Annotated[datetime, Indexed()] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "logs"
