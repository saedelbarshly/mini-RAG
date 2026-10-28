from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
import uuid
from qdrant_client import models, QdrantClient
from typing import List
from models.db_schemes import RetrievedDocument

class QdrantDBProvider(VectorDBInterface):
    
    def __init__(self, db_client: str, db_url: str = None, default_vector_size: int = 512, distance_method: str = None, index_threshold: int = 100):
        self.db_client = db_client
        self.db_url = db_url
        self.client = None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        else:
            self.distance_method = models.Distance.COSINE

        self.logger = logging.getLogger('uvicorn')

    async def connect(self):
        # local path mode locks the folder to one process, so multi-worker deployments need the server
        if self.db_url:
            self.client = QdrantClient(url=self.db_url)
        else:
            self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        if self.client is not None:
            self.client.close()
        self.client = None
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    async def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    async def delete_collection(self, collection_name: str):
        if await self.is_collection_existed(collection_name=collection_name):
            self.logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)

        return None

    async def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset:
            self.logger.info(f"Resetting collection: {collection_name}")
            _ = await self.delete_collection(collection_name=collection_name)

        if not await self.is_collection_existed(collection_name=collection_name):
            self.logger.info(f"Creating new Qdrant collection: {collection_name}")
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )
            self.logger.info(f"Collection created: {collection_name}")

            return True

        self.logger.info(f"Collection already exists, skipping create: {collection_name}")
        return False
            
            
    async def insert_one(self,
                   collection_name: str,
                   text: str,
                   vector: List,
                   metadata: dict = None,
                   record_id: str = None
                   ):

        if not await self.is_collection_existed(collection_name=collection_name):
            self.logger.error(F" Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        try:
            # Qdrant point ids must be an unsigned int or a UUID
            if record_id is None:
                record_id = str(uuid.uuid4())

            _ = self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=record_id,
                        vector=vector,
                        payload={
                            "text": text,
                            "metadata": metadata
                        }
                    )
                ]
            )

        except Exception as e:
            self.logger.error(f"Error while insert one: {e}")
            return False

        return True
    
    
    async def insert_many(self,
                    collection_name: str,
                    texts: List,
                    vectors: List,
                    metadata: List = None,
                    record_ids: List = None,
                    batch_size: int = 50
                    ):
        if not await self.is_collection_existed(collection_name=collection_name):
            self.logger.error(F" Can not insert batch record to non-existed collection: {collection_name}")
            return False
        
        if metadata is None:
            metadata = [None] * len(texts)

        if not (len(texts) == len(vectors) == len(metadata)) or \
                (record_ids is not None and len(record_ids) != len(texts)):
            self.logger.error("texts, vectors, metadata and record_ids must have the same length")
            return False
            
        # Qdrant point ids must be an unsigned int or a UUID
        if record_ids is None:
            # record_ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.PointStruct(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x],
                        "metadata": batch_metadata[x]
                    }
                 )
                for x in range(len(batch_texts))
            ]
            
            try:
                _ = self.client.upsert(
                    collection_name=collection_name,
                    points=batch_records
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True
        

    async def search_by_vector(self, collection_name: str, vector: List, limit: int = 5) -> List[RetrievedDocument]:
        
        results = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
            ).points
        
        if not results or len(results) == 0:
            return None

        return [
            RetrievedDocument(**{
                "score": result.score,
                "text": result.payload["text"]
            })
            for result in results
        ]

            