from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = db_client[DataBaseEnum.Collection_CHUNKS.value]


    async def create_chunk(self, chunk_data: dict) -> DataChunk:
        chunk = DataChunk(**chunk_data)
        result =    await self.collection.insert_one(chunk.dict())
        return chunk    


    async def get_chunk(self, chunk_id: str) -> DataChunk:
        chunk = await self.collection.find_one({"_id": ObjectId(chunk_id)})
        if chunk is None:
            return None 
        return DataChunk(**chunk)


    async def insert_chunks(self, chunks: list, batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            operations = [
                InsertOne(chunk.dict())
                for chunk in batch
            ]
            await self.collection.bulk_write(operations)

        return len(chunks)


    async def delete_chunks_by_project_id(self, project_id: str):
        result = await self.collection.delete_many({
            "chunk_project_id": ObjectId(project_id)
        })
        return result.deleted_count