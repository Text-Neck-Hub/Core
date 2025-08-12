from typing import Any, Sequence, Mapping, Union, List
from pydantic import BaseModel
from ..schemas.logs import Log as LogDto

from ..models.users import User, Log


class LogRepository:
    async def push_logs(
        self,
        user: Union[User, int],
        items: Sequence[Union[BaseModel, Mapping[str, Any]]],
    ) -> int:
        if not items:
            return 0

        u = await self._ensure_user(user)

        docs: List[Log] = []
        for item in items:
            if isinstance(item, BaseModel):
                data = self._dump_model(item)
            elif isinstance(item, Mapping):
                data = {k: v for k, v in item.items() if v is not None}
            else:
                continue

            angle = data.get("angle")
            shoulder_y_diff = data.get("shoulder_y_diff")
            shoulder_y_avg = data.get("shoulder_y_avg")
            logged_at = data.get("logged_at")

            if angle is None or shoulder_y_diff is None or shoulder_y_avg is None:
                continue

            try:
                angle = float(angle)
                shoulder_y_diff = float(shoulder_y_diff)
                shoulder_y_avg = float(shoulder_y_avg)
            except (TypeError, ValueError):
                continue

            logged_at = self._normalize_logged_at(logged_at)

            docs.append(
                Log(
                    user=u,
                    angle=angle,
                    shoulder_y_diff=shoulder_y_diff,
                    shoulder_y_avg=shoulder_y_avg,
                    logged_at=logged_at,
                )
            )

        if not docs:
            return 0

        res = await Log.insert_many(docs)
        if hasattr(res, "inserted_ids"):
            return len(res.inserted_ids)
        if isinstance(res, list):
            return len(res)
        return len(docs)

    async def get_logs(
        self,
        user: Union[User, int],
        limit: int = 100,
        skip: int = 0,
    ) -> List[Log]:
        return await Log.find(Log.user == user).skip(skip).limit(limit).project(LogDto).to_list()
