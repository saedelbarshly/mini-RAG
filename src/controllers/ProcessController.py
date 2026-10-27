from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import ProcessEnum
from typing import List
from dataclasses import dataclass

@dataclass
class Document:
    page_content: str
    metadata: dict
class ProcessController(BaseController):
    
    def __init__(self, project_id: int):
        super().__init__()
        
        self.project_id = project_id
        self.project_path = ProjectController().get_porject_path(project_id=project_id)
        
    
    def get_file_extension(self,file_id: str):
        return os.path.splitext(file_id)[-1].lower()
    
    def get_file_path(self, file_id: str):
        return os.path.join(
            self.project_path,
            file_id
        )

    def is_file_exists(self, file_id: str):
        return os.path.isfile(self.get_file_path(file_id=file_id))

    def get_file_loader(self, file_id: str):

        file_ext = self.get_file_extension(file_id=file_id)
        file_path = self.get_file_path(file_id=file_id)
        
        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        
        if file_ext == ProcessEnum.PDF.value:
            return PyMuPDFLoader(file_path)   
        
        return None
    
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader.load()

        return None
    
    
    def process_file_content(self, file_content: list, chunk_size: int=100, chunk_overlap: int=20):
        
        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]
        
        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]
        
        
        chunks = self.process_simpler_splitter(
            texts=file_content_texts,
            metadata=file_content_metadata,
            chunk_size=chunk_size
        )
        
        return chunks
    
    def process_simpler_splitter(self, texts: List[str], metadata: list[dict], chunk_size: int, splitter_tag: str="\n"):
        full_text = " ".join(texts)
        lines = [doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip()) > 1]
        
        chunks = []
        current_chunk = ""
        
        for line in lines:
            current_chunk += line + splitter_tag
            if len(current_chunk) >= chunk_size:
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={}
                ))
                
                current_chunk = ""
                
        
        if len(current_chunk) >= 0:
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata={}
            ))
        
        return chunks