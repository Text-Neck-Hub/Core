from typing import Any, Generic, Optional, Type, TypeVar, Sequence, Mapping, Union, Dict, List
from pydantic import BaseModel
from beanie import Document

TDoc = TypeVar("TDoc", bound=Document)


class Database(Generic[TDoc]):
    def __init__(self, model: Type[TDoc]):
        self.model = model

    async def save(self, document: TDoc) -> TDoc:
        await document.insert()
        return document

    async def get_all(self) -> List[TDoc]:
        return await self.model.find_all().to_list()

    async def get_by_id(self, id: Any) -> Optional[TDoc]:
        try:
            return await self.model.get(id)
        except Exception:
            return await self.model.find_one({"_id": id})

    async def push_many_by_id(
        self,
        id: Any,
        items: Sequence[Union[BaseModel, Mapping[str, Any]]],
        field: str = "angles_logs",
        slice_max: int = 5000,
        set_on_insert: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if not items:
            return

        payload: List[Dict[str, Any]] = []
        for item in items:
            if isinstance(item, BaseModel):
                data = item.model_dump(exclude_none=True) if hasattr(
                    item, "model_dump") else item.model_dump(exclude_none=True)
            elif isinstance(item, Mapping):
                data = {k: v for k, v in item.items() if v is not None}
            else:
                continue

            if data:
                payload.append(data)

        if not payload:
            return

        coll = self.model.get_motor_collection()

        update_doc: Dict[str, Any] = {
            "$push": {field: {"$each": payload, "$slice": -int(slice_max)}}
        }
        if set_on_insert:
            update_doc["$setOnInsert"] = dict(set_on_insert)

        await coll.update_one({"_id": id}, update_doc, upsert=True)
