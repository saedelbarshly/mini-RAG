from fastapi import FastAPI, APIRouter, Depends, UploadFile
from helpers.config import get_settings, Setting
from controllers import DataController

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)

@data_router.post("/upload/{project_id}")
async def uploadData(project_id: str, file: UploadFile, app_setting: Setting = Depends(get_settings)):
    # validate the file properties
    is_valid = DataController().validate_uploaded_file(file=file)
    return is_valid