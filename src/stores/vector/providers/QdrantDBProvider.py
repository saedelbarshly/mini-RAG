from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
import uuid
from qdrant_client import models, QdrantClient
from typing import List

class QdrantDBProvider(VectorDBInterface):
    
    def __init__(self, db_path: str, distance_method: str):
        self.db_path = db_path
        self.client = None
        
        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
            
        if distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT  
                 
        self.logger = logging.getLogger(__name__)

    def connect(self):
            self.client = QdrantClient(path=self.db_path)
    def disconnect(self):
        if self.client is not None:
            self.client.close()
        self.client = None
    
    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name=collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        
        return None
    
    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
            
        if not self.is_collection_existed(collection_name=collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )
            
            return True
        
        return False
            
            
    def insert_one(self,
                   collection_name: str,
                   text: str,
                   vector: List,
                   metadata: dict = None,
                   record_id: str = None
                   ):
        
        if not self.is_collection_existed(collection_name=collection_name):
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
    
    
    def insert_many(self,
                    collection_name: str,
                    texts: List,
                    vectors: List,
                    metadata: List = None,
                    record_ids: List = None,
                    batch_size: int = 50
                    ):
        if not self.is_collection_existed(collection_name=collection_name):
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
        

    def search_by_vector(self, collection_name: str, vector: List, limit: int = 5) -> List:
        return self.client.query_points(collection_name=collection_name, query=vector, limit=limit).points
        
        

            