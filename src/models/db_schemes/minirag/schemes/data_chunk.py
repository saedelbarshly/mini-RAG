from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel
import uuid


class DataChunk(SQLAlchemyBase):
    
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    chunk_text = Column(String, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    
    chunk_project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    chunk_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # relationship
    project = relationship("Project", back_populates="chunks")
    asset = relationship("Asset", back_populates="chunks")
    
    # index
    __table_args__= (
        Index("index_chunk_project_id", chunk_project_id),
        Index("index_chunk_asset_id", chunk_asset_id),
    )
    
    
    
            
class RetrievedDocument(BaseModel):
    text: str
    score: float    