

from datetime import datetime, timezone
from pydantic import Field
from beanie import Document, BackLink, Link
from typing import Annotated, List
from beanie import Document, Indexed


class User(Document):
    user_id: Annotated[int, Indexed(unique=True)]
    logs: List[BackLink["Log"]]

    class Settings:
        name = "users"


class Log(Document):
    user: Link[User]
    angle: float
    shoulder_y_diff: float
    shoulder_y_avg: float
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "logs"
