from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class Status(Enum):
    HEALTHY = 0
    CAUTION = 1
    DANGER = 2


class Angle(BaseModel):
    angle: int
    result: Status
    loged_at: datetime = datetime.now()
