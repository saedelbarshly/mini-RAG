from ..VectorDBEnums import VectorDBEnums, DistanceMethodEnums, PgVectorDistanceMethodEnums, PgVectorIndexTypeEnums, PgVectorTableSchemeEnums
from ..VectorDBInterface import VectorDBInterface
from models.db_schemes import RetrievedDocument
from typing import List
import logging
from sqlalchemy.sql import text as sql_text
import json


class PGVectorProvider(VectorDBInterface):
    def __init__(self, db_client, default_vector_size: int=512, distance_method: str = None, index_threshold: int = 100) -> None:
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold

        # map the generic distance method to the pgvector operator class used by the index
        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = PgVectorDistanceMethodEnums.DOT.value
        else:
            self.distance_method = PgVectorDistanceMethodEnums.COSINE.value

        self.pgvector_table_perfix = PgVectorTableSchemeEnums._PREFIX.value
        
        self.logger = logging.getLogger("uvicorn")
        
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"
        
        
        
    async def connect(self):
        # create the pgvector ext if not created and should be installed
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(
                    "SELECT 1 FROM pg_tables WHERE tablename = :collection_name"
                )
                result = await session.execute(list_tbl, {"collection_name": collection_name})
                record = result.scalar_one_or_none()

        return record is not None

    async def list_all_collections(self) -> List:
        records = []
        async with self.db_client() as session:
            async with session.begin():
                list_tbl = sql_text(
                    "SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix"
                )
                results = await session.execute(list_tbl, {"prefix": f"{self.pgvector_table_perfix}%"})
                records = results.scalars().all()

        return records
    
    
    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client() as session:
            async with session.begin():
                tabel_info_sql = sql_text('''
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE tablename = :collection_name
                ''')

                table_info = await session.execute(tabel_info_sql, {"collection_name": collection_name})
                table_data = table_info.fetchone()
                if not table_data:
                    return None

                # table names can not be bound as parameters, so it goes in the query string
                count_sql = sql_text(f'SELECT COUNT(*) FROM {collection_name}')
                record_count = await session.execute(count_sql)

                return {
                    "table_info": {
                        "schemaname": table_data[0],
                        "tablename": table_data[0],
                        "tableowner": table_data[0],
                        "tablespace": table_data[0],
                        "hasindexes": table_data[0],
                        },
                    "record_count": record_count.scalar_one()
                }

                
    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection:{collection_name}")
                delete_sql = sql_text(
                    f"DROP TABLE IF EXISTS {collection_name}"
                )
                await session.execute(delete_sql)

        return True


    async def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)

        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f'Creating collection: {collection_name}')
            async with self.db_client() as session:
                async with session.begin():
                    create_sql = sql_text(
                        f'CREATE TABLE {collection_name} ('
                        f'{PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY, '
                        f'{PgVectorTableSchemeEnums.TEXT.value} text, '
                        f'{PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}), '
                        f'{PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\', '
                        f'{PgVectorTableSchemeEnums.CHUNK_ID.value} integer UNIQUE, '
                        f'FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERENCES chunks(id)'
                        ')'
                    )

                    await session.execute(create_sql)
            
            return True
        return False  
    
    async def is_index_existed(self, collection_name: str) -> bool:
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                check_sql = sql_text('''
                    SELECT 1
                    FROM pg_indexes
                    WHERE tablename = :collection_name
                    AND indexname = :index_name
                ''')
                result = await session.execute(check_sql, {"collection_name": collection_name, "index_name": index_name})
                record = bool(result.scalar_one_or_none())

        return record

    async def create_vector_index(self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        is_index_existed = await self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            return False

        async with self.db_client() as session:
            async with session.begin():
                # skip small collections, a sequential scan is fast enough and ivfflat needs data to build its lists
                count_sql = sql_text(f'SELECT COUNT(*) FROM {collection_name}')
                result = await session.execute(count_sql)
                records_count = result.scalar_one()

                if records_count < self.index_threshold:
                    return False

                self.logger.info(f'Creating vector index for collection: {collection_name}')

                index_name = self.default_index_name(collection_name=collection_name)
                create_idx_sql = sql_text(
                    f'CREATE INDEX {index_name} ON {collection_name} '
                    f'USING {index_type} ({PgVectorTableSchemeEnums.VECTOR.value} {self.distance_method})'
                )

                await session.execute(create_idx_sql)

        self.logger.info(f'Vector index created for collection: {collection_name}')
        return True

    async def reset_vector_index(self, collection_name: str, index_type: str = PgVectorIndexTypeEnums.HNSW.value):
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f'Dropping vector index for collection: {collection_name}')
                drop_idx_sql = sql_text(f'DROP INDEX IF EXISTS {index_name}')
                await session.execute(drop_idx_sql)

        return await self.create_vector_index(collection_name=collection_name, index_type=index_type)

    def _upsert_on_chunk_id_sql(self) -> str:
        # re-indexing the same chunk replaces its row (like qdrant upsert) instead of adding a duplicate
        return (
            f'ON CONFLICT ({PgVectorTableSchemeEnums.CHUNK_ID.value}) DO UPDATE SET '
            f'{PgVectorTableSchemeEnums.TEXT.value} = EXCLUDED.{PgVectorTableSchemeEnums.TEXT.value}, '
            f'{PgVectorTableSchemeEnums.VECTOR.value} = EXCLUDED.{PgVectorTableSchemeEnums.VECTOR.value}, '
            f'{PgVectorTableSchemeEnums.METADATA.value} = EXCLUDED.{PgVectorTableSchemeEnums.METADATA.value}'
        )

    async def insert_one(self, collection_name: str, text: str, vector: List, metadata: dict = None, record_id: str = None):      
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f'Can not insert new record to non-existed collection: {collection_name}')
            return False
        
        if not record_id:
            self.logger.error(f'Can not insert new record without chunk_id: {collection_name}')
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                    f'INSERT INTO {collection_name} '
                    f'({PgVectorTableSchemeEnums.TEXT.value}, {PgVectorTableSchemeEnums.VECTOR.value}, {PgVectorTableSchemeEnums.METADATA.value}, {PgVectorTableSchemeEnums.CHUNK_ID.value}) '
                    'VALUES (:text, :vector, :metadata, :chunk_id) '
                    f'{self._upsert_on_chunk_id_sql()}'
                )

                await session.execute(insert_sql, {
                    'text': text,
                    'vector': "[" + ",".join([str(v) for v in vector]) + "]", # postgresql take vector as string
                    'metadata': json.dumps(metadata) if metadata is not None else '{}',
                    'chunk_id': record_id
                })
                
        return True
    
    
    async def insert_many(self, collection_name: str, texts: List, vectors: List, metadata: List = None, record_ids: List = None, batch_size: int = 50):
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f'Can not insert batch records to non-existed collection: {collection_name}')
            return False

        if record_ids is None:
            self.logger.error(f'Can not insert batch records without chunk_ids: {collection_name}')
            return False

        if metadata is None:
            metadata = [None] * len(texts)

        if not (len(texts) == len(vectors) == len(metadata) == len(record_ids)):
            self.logger.error('texts, vectors, metadata and record_ids must have the same length')
            return False

        insert_sql = sql_text(
            f'INSERT INTO {collection_name} '
            f'({PgVectorTableSchemeEnums.TEXT.value}, {PgVectorTableSchemeEnums.VECTOR.value}, {PgVectorTableSchemeEnums.METADATA.value}, {PgVectorTableSchemeEnums.CHUNK_ID.value}) '
            'VALUES (:text, :vector, :metadata, :chunk_id) '
            f'{self._upsert_on_chunk_id_sql()}'
        )

        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(texts), batch_size):
                    batch_end = i + batch_size
                    batch_texts = texts[i:batch_end]
                    batch_vectors = vectors[i:batch_end]
                    batch_metadata = metadata[i:batch_end]
                    batch_record_ids = record_ids[i:batch_end]

                    batch_values = [
                        {
                            'text': batch_texts[x],
                            'vector': "[" + ",".join([str(v) for v in batch_vectors[x]]) + "]", # postgresql take vector as string
                            'metadata': json.dumps(batch_metadata[x]) if batch_metadata[x] is not None else None,
                            'chunk_id': batch_record_ids[x]
                        }
                        for x in range(len(batch_texts))
                    ]

                    # passing a list of dicts makes sqlalchemy run it as executemany
                    await session.execute(insert_sql, batch_values)

        # build the index only after the insert transaction commits: CREATE INDEX runs on
        # another connection and would wait forever on the row locks held by this transaction
        await self.create_vector_index(collection_name=collection_name)

        return True
    
    async def search_by_vector(self, collection_name: str, vector: List, limit: int) -> List[RetrievedDocument]:
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f'Can not search in non-existed collection: {collection_name}')
            return None

        vector = "[" + ",".join([str(v) for v in vector]) + "]" # postgresql take vector as string
        async with self.db_client() as session:
            async with session.begin():
                # order by the distance itself (not the score alias) so the vector index can be used
                search_sql = sql_text(
                    f'SELECT {PgVectorTableSchemeEnums.TEXT.value} AS text, '
                    f'1 - ({PgVectorTableSchemeEnums.VECTOR.value} <=> :vector) AS score '
                    f'FROM {collection_name} '
                    f'ORDER BY {PgVectorTableSchemeEnums.VECTOR.value} <=> :vector '
                    'LIMIT :limit'
                )

                results = await session.execute(search_sql, {"vector": vector, "limit": limit})
                records = results.fetchall()

        if not records:
            return None

        return [
            RetrievedDocument(
                text=record.text,
                score=record.score
            )
            for record in records
        ]