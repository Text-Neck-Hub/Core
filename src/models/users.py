
from typing import List
from ..schemas.angles import Angle
from beanie import Document, Link, Indexed
from pydantic import Field


class User(Document):
    user_id: int = Indexed(int, unique=True)
    angles_logs: List[Link[Angle]] = Field(default_factory=list)

    class Settings:
        name = "users"
