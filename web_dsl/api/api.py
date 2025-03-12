import os
import re
import uuid
import base64
import tarfile
import subprocess
from fastapi import FastAPI, File, UploadFile, status, HTTPException, Security, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from web_dsl.language import build_model
from web_dsl.generate import generate_frontend

API_KEY = os.getenv("API_KEY", "API_KEY")
TMP_DIR = "./tmp/"

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

api.mount("/generated", StaticFiles(directory=TMP_DIR, html=True), name="generated")


class ValidationModel(BaseModel):
    name: str
    model: str


class TransformationModel(BaseModel):
    name: str
    model: str


@api.post("/validate", tags=["Validation"])
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
        resp["message"] = "Model validation success"
    except Exception as e:
        print("Exception while validating model. Validation failed!!")
        print(e)
        resp["status"] = 404
        resp["message"] = str(e)
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    return resp


@api.post("/validate/file", tags=["Validation"])
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
    fpath = os.path.join(TMP_DIR, f"model_for_validation-{u_id}.dsl")
    with open(fpath, "w") as f:
        f.write(fd.read().decode("utf8"))
    try:
        model = build_model(fpath)
        resp["message"] = "Model validation success"
    except Exception as e:
        resp["status"] = 404
        resp["message"] = e
    return resp


@api.get("/validate/base64", tags=["Validation"])
async def validate_b64(fenc: str = "", api_key: str = Security(get_api_key)):
    if len(fenc) == 0:
        return 404
    resp = {"status": 200, "message": ""}
    fdec = base64.b64decode(fenc)
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, "model_for_validation-{}.dsl".format(u_id))
    with open(fpath, "wb") as f:
        f.write(fdec)
    try:
        model = build_model(fpath)
        resp["message"] = "Model validation success"

    except Exception as e:
        resp["status"] = 404
        resp["message"] = e
    return resp


@api.post("/generate", tags=["Generation"])
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


@api.post("/generate/file", tags=["Generation"])
async def gen_from_file(
    model_file: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    print(
        f"Generate for request: file=<{model_file.filename}>,"
        + f" descriptor=<{model_file.file}>"
    )
    resp = {"status": 200, "message": ""}
    fd = model_file.file
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.dsl")
    tarball_path = os.path.join(TMP_DIR, f"{u_id}.tar.gz")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")
    with open(model_path, "w") as f:
        f.write(fd.read().decode("utf8"))
    try:
        out_dir = generate_frontend(model_path, gen_path)
        make_tarball(tarball_path, out_dir)
        print(f"Sending tarball {tarball_path}")
        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )
    except Exception as e:
        print(e)
        resp["status"] = 404
        return resp


@api.post("/generate/preview", tags=["Preview"])
async def gen_from_file_preview(
    gen_model: TransformationModel = Body(...), api_key: str = Security(get_api_key)
):
    model = gen_model.model
    resp = {"status": 200, "message": ""}
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.dsl")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")

    if not os.path.exists(gen_path):
        os.mkdir(gen_path)
    with open(model_path, "w") as f:
        f.write(model)

    with open(model_path, "w") as f:
        f.write(model)
    try:
        out_dir = generate_frontend(model_path, gen_path)
        print("Generated frontend at:", out_dir)
    except Exception as e:
        print(e)
        resp["status"] = 404
        return resp
    try:
        # Install dependencies.
        print("Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=out_dir, check=True)
        # Build the app.
        print("Building the app...")
        subprocess.run(["npm", "run", "build"], cwd=out_dir, check=True)

        build_dir = os.path.join(out_dir, "dist")
        base_url = f"/generated/gen-{u_id}/dist/"
        inject_base_href(build_dir, base_url)
        frontend_url = f"/generated/gen-{u_id}/dist/"
        return JSONResponse(
            content={"frontend_url": frontend_url},
            status_code=200,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Codintxt.Transformation error: {e}"
        )


@api.post("/generate/file/preview", tags=["Preview"])
async def gen_from_file_preview(
    model_file: UploadFile = File(...), api_key: str = Security(get_api_key)
):
    print(
        f"Generate for request: file=<{model_file.filename}>,"
        + f" descriptor=<{model_file.file}>"
    )
    resp = {"status": 200, "message": ""}
    fd = model_file.file
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.dsl")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")

    with open(model_path, "w") as f:
        f.write(fd.read().decode("utf8"))
    try:
        out_dir = generate_frontend(model_path, gen_path)
        print("Generated frontend at:", out_dir)
    except Exception as e:
        print(e)
        resp["status"] = 404
        return resp
    try:
        # Install dependencies.
        print("Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=out_dir, check=True)
        # Build the app.
        print("Building the app...")
        subprocess.run(["npm", "run", "build"], cwd=out_dir, check=True)

        build_dir = os.path.join(out_dir, "dist")
        base_url = f"/generated/gen-{u_id}/dist/"
        inject_base_href(build_dir, base_url)
        frontend_url = f"/generated/gen-{u_id}/dist/"
        return JSONResponse(
            content={"frontend_url": frontend_url},
            status_code=200,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Codintxt.Transformation error: {e}"
        )


def inject_base_href(build_dir: str, base_url: str):
    index_path = os.path.join(build_dir, "index.html")
    with open(index_path, "r+", encoding="utf8") as f:
        content = f.read()

        # Inject <base> tag and <script> for window.__BASE_PATH__
        script_tag = f"""
        <script>
          window.__BASE_PATH__ = "{base_url}";
        </script>
        """
        content = content.replace(
            "<head>", f'<head>{script_tag}<base href="{base_url}">'
        )

        # Fix asset paths to be relative to `base_url`
        content = re.sub(
            r'(<script[^>]+src=")(/assets/)', rf"\1{base_url}assets/", content
        )
        content = re.sub(
            r'(<link[^>]+href=")(/assets/)', rf"\1{base_url}assets/", content
        )

        f.seek(0)
        f.write(content)
        f.truncate()
