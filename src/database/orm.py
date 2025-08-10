from typing import Any, Generic, List, Optional, Type, TypeVar, Union, Dict
from beanie import Document, PydanticObjectId
from pydantic import BaseModel

TDoc = TypeVar("TDoc", bound=Document)


class Database(Generic[TDoc]):
    def __init__(self, model: Type[TDoc]):
        self.model = model

    async def save(self, document: TDoc) -> TDoc:
        await document.create()
        return document

    async def get_all(self) -> List[TDoc]:
        return await self.model.find_all().to_list()

    async def get_by_id(self, id: Union[PydanticObjectId, str]) -> Optional[TDoc]:
        return await self.model.get(id)

    async def find_one(self, filter_: Dict[str, Any]) -> Optional[TDoc]:
        return await self.model.find_one(filter_)

    async def delete(self, id: Union[PydanticObjectId, str]) -> bool:
        doc = await self.model.get(id)
        if not doc:
            return False
        await doc.delete()
        return True

    async def update(
        self,
        id: Union[PydanticObjectId, str],
        body: Union[BaseModel, Dict[str, Any]]
    ) -> Optional[TDoc]:
        doc = await self.model.get(id)
        if not doc:
            return None

        if isinstance(body, BaseModel):
            data = body.model_dump(exclude_none=True)
        else:
            data = {k: v for k, v in body.items() if v is not None}

        if not data:
            return await self.model.get(id)

        await doc.update({"$set": data})
        return await self.model.get(id)

    async def push_many_by_user_id(
        self,
        user_id: int,
        items: List[BaseModel] | List[Dict[str, Any]],
        slice_max: int = 5000
    ) -> Optional[TDoc]:
        if not items:
            return await self.model.find_one(self.model.user_id == user_id)

        payload: List[Dict[str, Any]] = []
        for it in items:
            if isinstance(it, BaseModel):
                if hasattr(it, "model_dump"):
                    data = it.model_dump(exclude_none=True)
                else:
                    data = it.dict(exclude_none=True)
            else:
                data = {k: v for k, v in it.items() if v is not None}
            if data:
                payload.append(data)

        if not payload:
            return await self.model.find_one(self.model.user_id == user_id)

        coll = self.model.get_motor_collection()
        await coll.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": {"user_id": user_id, "logs": []},
                "$push": {"logs": {"$each": payload, "$slice": -int(slice_max)}}
            },
            upsert=True
        )
        return await self.model.find_one(self.model.user_id == user_id)
