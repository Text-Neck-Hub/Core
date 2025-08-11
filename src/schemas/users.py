from pydantic import BaseModel
from typing import List
from .angles import Angle


class User(BaseModel):
    user_id: int
    angles_logs: List[Angle]
