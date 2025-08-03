from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class NeckStatus(Enum):
    HEALTHY = 0
    CAUTION = 1
    DANGER = 2


class Angle(BaseModel):
    angle: int
    result: NeckStatus
    loged_at: datetime = datetime.now()
