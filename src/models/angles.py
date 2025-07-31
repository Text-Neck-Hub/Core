from beanie import Document, PydanticObjectId
from datetime import datetime
from enum import Enum


class NeckStatus(Enum):
    HEALTHY = 0
    CAUTION = 1
    DANGER = 2


class NeckAngleLog(Document):
    user_id: PydanticObjectId
    angle: int
    result: NeckStatus
    loged_at: datetime = datetime.now()

    class Settings:
        name = "angles"


class NeckAngleSetting(Document):
    threshold: int
    healthy_range: int
    caution_range: int
    danger_range: int

    class Settings:
        name = "settings"
