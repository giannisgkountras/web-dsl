from fastapi import APIRouter, UploadFile, HTTPException, File, Security
from ..models import ValidationModel
from ..utils import get_unique_id, save_text_to_file, save_upload_file
from web_dsl.language import build_model
import os
import traceback
from ..config import get_api_key, TMP_DIR

router = APIRouter(tags=["Validation"])


@router.post("/validate", tags=["Validation"], status_code=201)
async def validate_model(model: ValidationModel, api_key: str = Security(get_api_key)):
    if not model.model:
        raise HTTPException(status_code=404, detail="Empty model content")
    uid = get_unique_id()
    file_path = os.path.join(TMP_DIR, f"model_for_validation-{uid}.wdsl")
    save_text_to_file(model.model, file_path)
    try:
        build_model(file_path)
        return {"status": 200, "message": "Model validation success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")


@router.post("/validate/file", tags=["Validation"], status_code=201)
async def validate_model_file(
    file: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    uid = get_unique_id()
    file_path = os.path.join(TMP_DIR, f"model_for_validation-{uid}.wdsl")
    save_upload_file(file, file_path)
    try:
        build_model(file_path)
        return {"status": 200, "message": "Model validation success"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
