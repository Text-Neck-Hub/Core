from typing import Optional
from ..models.users import User


class UserRepository:
    async def get_by_user_id(self, user_id: int) -> Optional[User]:
        return await User.find_one(User.user_id == user_id)

    async def get_or_create_by_user_id(self, user_id: int) -> User:
        user = await self.get_by_user_id(user_id)
        if user:
            return user
        try:
            return await User(user_id=user_id).insert()
        except Exception:
            return await self.get_by_user_id(user_id)
