
from typing import List
from ..schemas import Angle
from beanie import Document, Link
from pydantic import Field
from ..schemas.options import Option


class User(Document):
    user_id: int = Field(default=-1)
    options: List[Link[Option]] = Field(default_factory=list)
    angles_logs: List[Link[Angle]] = Field(default_factory=list)

    class Settings:
        name = "users"
