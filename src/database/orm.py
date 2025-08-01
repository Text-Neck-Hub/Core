from beanie import Document


class Database:
    def __init__(self, model: Document):
        self.model = model

    async def save(self, document: Document) -> None:
        await document.create()
        return

    async def get_all(self) -> list:

        docs = await self.model.find_all().to_list()
        return docs

    async def delete(self, id: int):
        doc = await self.model.get(id)
        await doc.delete()

    async def get(self, id: int):
        doc = await self.model.get(id)
        return doc

    async def update(self, id: int, body):
        doc = await self.model.get(id)
        body = body.model_dump()
        body = {"$set": {k: v for k, v in body.items() if v is not None}}
        await doc.update(body)
