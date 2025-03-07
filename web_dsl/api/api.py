import os
import uuid

from fastapi import FastAPI, File, UploadFile, status, HTTPException, Security, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from web_dsl.language import build_model

API_KEY = os.getenv("API_KEY", "API_KEY")
TMP_DIR = "/tmp/goaldsl"

if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)

api_keys = [API_KEY]
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidationModel(BaseModel):
    name: str
    model: str


@api.post("/validate")
async def validate(model: ValidationModel, api_key: str = Security(get_api_key)):
    text = model.model
    name = model.name

    if len(text) == 0:
        return 404

    resp = {"status": 200, "message": ""}
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, f"model_for_validation-{u_id}.dsl")

    with open(fpath, "w") as f:
        f.write(text)
    try:
        model = build_model(fpath)
        print("Model validation success!!")
        print(model)
        resp["message"] = "Model validation success"
    except Exception as e:
        print("Exception while validating model. Validation failed!!")
        print(e)
        resp["status"] = 404
        resp["message"] = str(e)
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    return resp
