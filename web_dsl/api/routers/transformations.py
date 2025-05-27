import os
import traceback
from fastapi import UploadFile, HTTPException, File, Security, APIRouter
from fastapi.responses import FileResponse
from ..utils import (
    get_unique_id,
    save_text_to_file,
    save_upload_file,
)
from web_dsl.m2m.openapi_to_webdsl import transform_openapi_to_webdsl
from web_dsl.m2m.goaldsl_to_webdsl import transform_goaldsl_to_webdsl
from web_dsl.m2m.asyncapi_to_webdsl import transform_asyncapi_to_webdsl
from ..config import get_api_key, TMP_DIR


router = APIRouter(tags=["Transformations"])


@router.post("/transform/openapi")
async def generate_from_model(
    openapi_model: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    uid = get_unique_id()
    openapi_path = os.path.join(TMP_DIR, f"openapi-{uid}.yaml")
    web_dsl_path = os.path.join(TMP_DIR, f"webdsl-{uid}.wdsl")

    save_upload_file(openapi_model, openapi_path)

    try:
        web_dsl_model = transform_openapi_to_webdsl(openapi_path)
        save_text_to_file(web_dsl_model, web_dsl_path)
        print(f"Generated WDSL model: {web_dsl_path}")
        return FileResponse(
            path=web_dsl_path,
            filename=os.path.basename(web_dsl_path),
            media_type="text/plain",  # Use correct MIME type
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


@router.post("/transform/goaldsl")
async def generate_from_model(
    goaldsl_model: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    uid = get_unique_id()
    goaldsl_path = os.path.join(TMP_DIR, f"goaldsl-{uid}.goal")
    web_dsl_path = os.path.join(TMP_DIR, f"webdsl-{uid}.wdsl")

    save_upload_file(goaldsl_model, goaldsl_path)

    try:
        web_dsl_model = transform_goaldsl_to_webdsl(goaldsl_path)
        save_text_to_file(web_dsl_model, web_dsl_path)
        print(f"Generated WDSL model: {web_dsl_path}")
        return FileResponse(
            path=web_dsl_path,
            filename=os.path.basename(web_dsl_path),
            media_type="text/plain",  # Use correct MIME type
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


@router.post("/transform/asyncapi")
async def generate_from_model(
    asyncapi_model: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    uid = get_unique_id()
    asyncapi_path = os.path.join(TMP_DIR, f"openapi-{uid}.yaml")
    web_dsl_path = os.path.join(TMP_DIR, f"webdsl-{uid}.wdsl")

    save_upload_file(asyncapi_model, asyncapi_path)

    try:
        web_dsl_model = transform_asyncapi_to_webdsl(asyncapi_path)
        save_text_to_file(web_dsl_model, web_dsl_path)
        print(f"Generated WDSL model: {web_dsl_path}")
        return FileResponse(
            path=web_dsl_path,
            filename=os.path.basename(web_dsl_path),
            media_type="text/plain",  # Use correct MIME type
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")
