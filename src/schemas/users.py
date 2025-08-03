from pydantic import BaseModel
from typing import List
from .angles import Angle
from .options import Option


class User(BaseModel):
    user_id: int
    options: List[Option]
    logs: List[Angle]
