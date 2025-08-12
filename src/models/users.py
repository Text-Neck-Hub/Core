
from typing import List, Annotated
from .logs import Log
from beanie import Document, Indexed, Link
from pydantic import Field


class User(Document):
    user_id: Annotated[int, Indexed(unique=True)]
    logs: List[Link[Log]] = Field(default_factory=list)

    class Settings:
        name = "users"
