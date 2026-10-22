from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import delete

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = db_client


    @classmethod
    async def create_instance(cls, db_client):
        instance = cls(db_client)
        return instance


    async def create_chunk(self, chunk: DataChunk) -> DataChunk:
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)

            await session.refresh(chunk)

        return chunk


    async def get_chunk(self, chunk_id: int) -> DataChunk:
        async with self.db_client() as session:
            query = select(DataChunk).where(DataChunk.id == chunk_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()


    async def insert_chunks(self, chunks: list, batch_size: int = 100):
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
                    await session.flush()

        return len(chunks)


    async def delete_chunks_by_project_id(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(query)

        return result.rowcount

    async def get_project_chunk(self, project_id: int, page_no: int=1, page_size: int=50) -> list[DataChunk]:
        async with self.db_client() as session:
            query = select(DataChunk).where(
                DataChunk.chunk_project_id == project_id
            ).order_by(DataChunk.id).offset(
                (page_no-1) * page_size
            ).limit(page_size)

            result = await session.execute(query)
            return result.scalars().all()
