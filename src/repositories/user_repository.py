from typing import Optional
from pymongo import ReturnDocument
from ..models.users import User


class UserRepository:
    async def get_by_user_id(self, user_id: int) -> Optional[User]:
        return await User.find_one(User.user_id == user_id)

    async def get_or_create_by_user_id(self, user_id: int) -> None:

        await User.get_motor_collection().find_one_and_update(
            {"user_id": user_id},
            {"$setOnInsert": {"user_id": user_id}},
            upsert=True,
        )

        return
