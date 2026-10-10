from pydantic import BaseModel, Field, Validator
from typing import Optional
from bson.objectid import ObjectId


class DataChunk(BaseModel):
    _id: Optional[ObjectId]
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: list
    chunk_order: str = Field(..., gt=0)
    chunk_project_id: ObjectId
    
    class Config:
           arbitrary_types_allowed = True  #to ignor object id or unknow error 