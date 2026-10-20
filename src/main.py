from fastapi import FastAPI
from routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMFactory import LLMFactory
from stores.vector.VectorDBFactory import VectorDBFactory
from stores.llm.templates.template_parser import TemplateParser

app = FastAPI()

@app.on_event("startup")
async def startup_db_clinet():
    settings = get_settings()
    
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLMFactory(settings)
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODLE_ID)
    
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID, embedding_size=settings.EMBEDDING_MODEL_SIZE)
    
    
    vector_db_provider_factory = VectorDBFactory(settings)
    app.vector_db_client = vector_db_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
    if app.vector_db_client is None:
        raise ValueError(f"Unsupported VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND!r}")
    app.vector_db_client.connect()
    
    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG
    )
    

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()
    app.vector_db_client.disconnect()


app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)


