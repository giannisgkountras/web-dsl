import os
import uuid
import base64
import tarfile

from fastapi import FastAPI, File, UploadFile, status, HTTPException, Security, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from web_dsl.language import build_model
from web_dsl.generate import generate_frontend

API_KEY = os.getenv("API_KEY", "API_KEY")

TMP_DIR = "/tmp/webdsl"

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


def make_tarball(fout, source_dir):
    with tarfile.open(fout, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


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


class TransformationModel(BaseModel):
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


@api.post("/validate/file")
async def validate_file(
    file: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    print(
        f"Validation for request: file=<{file.filename}>,"
        + f" descriptor=<{file.file}>"
    )
    resp = {"status": 200, "message": ""}
    fd = file.file
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, f"model_for_validation-{u_id}.goal")
    with open(fpath, "w") as f:
        f.write(fd.read().decode("utf8"))
    try:
        model = build_model(fpath)
    except Exception as e:
        resp["status"] = 404
        resp["message"] = e
    return resp


@api.get("/validate/base64")
async def validate_b64(fenc: str = "", api_key: str = Security(get_api_key)):
    if len(fenc) == 0:
        return 404
    resp = {"status": 200, "message": ""}
    fdec = base64.b64decode(fenc)
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, "model_for_validation-{}.goal".format(u_id))
    with open(fpath, "wb") as f:
        f.write(fdec)
    try:
        model = build_model(fpath)
    except Exception as e:
        resp["status"] = 404
        resp["message"] = e
    return resp


@api.post("/generate")
async def gen_from_model(
    gen_model: TransformationModel = Body(...),
    api_key: str = Security(get_api_key),
):
    resp = {"status": 200, "message": "", "model_json": ""}
    model = gen_model.model
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.dsl")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")

    if not os.path.exists(gen_path):
        os.mkdir(gen_path)
    with open(model_path, "w") as f:
        f.write(model)

    tarball_path = os.path.join(TMP_DIR, f"{u_id}.tar.gz")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")

    try:
        out_dir = generate_frontend(model_path, gen_path)
        make_tarball(tarball_path, out_dir)
        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Codintxt.Transformation error: {e}"
        )
