from typing import Any, Sequence, Mapping, Union, List, Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from ..models.users import User
from ..models.logs import Log


class LogRepository:
    async def push_logs(
        self,
        user: Union[User, int],
        items: Sequence[Union[BaseModel, Mapping[str, Any]]],
    ) -> int:
        if not items:
            return 0

        if isinstance(user, int):
            u = await User.find_one(User.user_id == user)
            if not u:
                u = await User(user_id=user).insert()
        else:
            u = user

        docs: List[Log] = []

        for item in items:
            if isinstance(item, BaseModel):
                data = item.model_dump(exclude_none=True) if hasattr(
                    item, "model_dump") else item.model_dump(exclude_none=True)
            elif isinstance(item, Mapping):
                data = {k: v for k, v in item.items() if v is not None}
            else:
                continue

            if {"angle", "shoulder_y_diff", "shoulder_y_avg", "logged_at"}.issubset(data.keys()):
                docs.append(Log(user=u, **data))

        if not docs:
            return 0

        res = await Log.insert_many(docs)
        return len(res)
