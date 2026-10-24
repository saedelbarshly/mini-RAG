from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Setting(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int
    MONGODB_URL: str
    MONGODB_DATABASE: str
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPEN_AI_KEY: str = None
    OPEND_AI_URL: str = None
    COHERE_API_KEY: str = None

    GENERATION_MODLE_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None

    INPUT_DEFAULT_MAX_CHARACTERS: int = None
    GENERATION_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_TEMPERATURE: float = None
    
    VECTOR_DB_BACKEND_LITREAL: List[str] = None
    VECTOR_DB_BACKEND: str
    VECTOR_DB_NAME: str
    VECTOR_DB_DISTANCE_METHOD: Optional[str] = None
    VECTOR_DB_URL: Optional[str] = None
    VECTOR_DB_PGVECTOR_INDEX_THRESHOLD: int

    POSTGRES_USERNAME: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_MAIN_DATABASE: Optional[str] = None

    PRIMARY_LANG: str="en"
    DEFAULT_LANG: str="en"

    class Config:
        env_file = ".env"

def get_settings():
    return Setting()