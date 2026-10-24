from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from typing import List
from stores.llm.LLMEnums import DocumentTypeEnum
import json
class NLPController(BaseController):
    def __init__(self, vector_db_client, generation_client, embedding_client, template_parser):
        super().__init__()
        
        self.vector_db_client = vector_db_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        
    
    def create_collection_name(self, project_id: int):
        return f"collection_{self.vector_db_client.default_vector_size}_{project_id}".strip()
    
    
    async def reset_vector_db_collection(self, project_id: int):
        collection_name = self.create_collection_name(project_id=project_id)
        return await self.vector_db_client.delete_collection(collection_name=collection_name)


    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.id)
        collection_info = await self.vector_db_client.get_collection_info(collection_name=collection_name)
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
    
    
    async def index_into_vector_db(self, project: Project, chunks: List[DataChunk], chunks_ids: List[int], do_reset: bool = False):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.id)
        
        #step2: mange items
        texts = [ c.chunk_text for c in chunks]
        metadata = [ c.chunk_metadata for c in chunks]

        # embed the whole page in one call instead of one call per chunk
        vectors = self.embedding_client.embed_text(
            text=texts,
            document_type=DocumentTypeEnum.DOCUMENT.value
        )

        if not vectors or len(vectors) != len(texts):
            return False
        
        #step3: create collection if not exists
        _ = await self.vector_db_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )
        
        #step4: insert into vector db
        _ = await self.vector_db_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
            record_ids=chunks_ids
        )
        
        return True
    
    
    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 50):
        
        collection_name = self.create_collection_name(project_id=project.id)

        # embed_text returns a list of vectors, so send a one-item list and take the first
        vectors = self.embedding_client.embed_text(
                text=[text],
                document_type=DocumentTypeEnum.QUERY.value
            )

        if not vectors or len(vectors) == 0:
            return False

        vector = vectors[0]
        
        #setp:3 make search
        
        results = await self.vector_db_client.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit
        )
        
        if not results:
            return False
        
        return results
        
        
    async def answer_rag_question(self, project: Project, query: str, limit=10):
        answer, full_prompt,chat_history = None, None , None
        retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit
        )
        
        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt,chat_history
        
        # step2: construct LLM prompt
        
        system_prompt = self.template_parser.get(
            "rag", "system_prompt"
        )
        
        document_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.text),
            })
           for idx, doc in enumerate(retrieved_documents)
        ])
        
        footer_prompt = self.template_parser.get(
            "rag", "footer_prompt",{
                "query": query
            }
        )
        
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]
        
        full_prompt = "\n\n".join([document_prompts, footer_prompt])
        
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )
        
        return answer, full_prompt,chat_history 
        
        
        