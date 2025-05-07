import os
import re
import uuid
import base64
import tarfile
import subprocess
import time
import shutil

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    status,
    HTTPException,
    Security,
    Body,
    BackgroundTasks,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from web_dsl.language import build_model
from web_dsl.generate import generate

# Load the .env file
load_dotenv()

API_KEY = os.getenv("API_KEY", "API_KEY")
TMP_DIR = "./tmp/"
CLEANUP_THRESHOLD = 60 * 15  # 15m in seconds

os.makedirs(TMP_DIR, exist_ok=True)

api_keys = [API_KEY]
api_key_header = APIKeyHeader(name="X-API-Key")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/generated", StaticFiles(directory=TMP_DIR, html=True), name="generated")


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
    )


def get_unique_id() -> str:
    return uuid.uuid4().hex[:8]


def make_tarball(output_path: str, source_dir: str) -> None:
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def save_text_to_file(text: str, file_path: str, mode: str = "w") -> None:
    with open(file_path, mode) as f:
        f.write(text)


def save_upload_file(file: UploadFile, file_path: str) -> None:
    content = file.file.read().decode("utf8")
    save_text_to_file(content, file_path)


def save_base64_to_file(encoded_str: str, file_path: str) -> None:
    decoded = base64.b64decode(encoded_str)
    with open(file_path, "wb") as f:
        f.write(decoded)


def inject_base_href(build_dir: str, base_url: str) -> None:
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


def cleanup_old_generations():
    now = time.time()
    for entry in os.listdir(TMP_DIR):
        path = os.path.join(TMP_DIR, entry)
        # Check if the file/directory is older than our threshold.
        if os.path.getmtime(path) < now - CLEANUP_THRESHOLD:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                print(f"Deleted old generation: {path}")
            except Exception as e:
                print(f"Error cleaning up {path}: {e}")


class ValidationModel(BaseModel):
    name: str
    model: str


class TransformationModel(BaseModel):
    name: str
    model: str


# ============= Validation Endpoints =============
@app.post("/validate", tags=["Validation"])
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


@app.post("/validate/file", tags=["Validation"])
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
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")


@app.get("/validate/base64", tags=["Validation"])
async def validate_model_base64(fenc: str = "", api_key: str = Security(get_api_key)):
    if not fenc:
        raise HTTPException(status_code=404, detail="Empty base64 string")
    uid = get_unique_id()
    file_path = os.path.join(TMP_DIR, f"model_for_validation-{uid}.wdsl")
    save_base64_to_file(fenc, file_path)
    try:
        build_model(file_path)
        return {"status": 200, "message": "Model validation success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")


# ============= Generation Endpoints =============
@app.post("/generate", tags=["Generation"])
async def generate_from_model(
    gen_model: TransformationModel = Body(...), api_key: str = Security(get_api_key)
):
    uid = get_unique_id()
    model_path = os.path.join(TMP_DIR, f"model-{uid}.wdsl")
    gen_dir = os.path.join(TMP_DIR, f"gen-{uid}")
    os.makedirs(gen_dir, exist_ok=True)
    save_text_to_file(gen_model.model, model_path)
    tarball_path = os.path.join(TMP_DIR, f"{uid}.tar.gz")
    try:
        out_dir = generate(model_path, gen_dir)
        make_tarball(tarball_path, out_dir)
        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


@app.post("/generate/file", tags=["Generation"])
async def generate_from_file(
    model_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: str = Security(get_api_key),
):
    background_tasks.add_task(cleanup_old_generations)
    uid = get_unique_id()
    model_path = os.path.join(TMP_DIR, f"model-{uid}.wdsl")
    gen_dir = os.path.join(TMP_DIR, f"gen-{uid}")
    os.makedirs(gen_dir, exist_ok=True)
    save_upload_file(model_file, model_path)
    tarball_path = os.path.join(TMP_DIR, f"{uid}.tar.gz")
    try:
        out_dir = generate(model_path, gen_dir)
        make_tarball(tarball_path, out_dir)
        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


# ============= Preview Endpoints =============
@app.post("/generate/preview", tags=["Preview"])
async def generate_preview_from_model(
    gen_model: TransformationModel = Body(...),
    api_key: str = Security(get_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    uid = get_unique_id()
    model_path = os.path.join(TMP_DIR, f"model-{uid}.wdsl")
    gen_dir = os.path.join(TMP_DIR, f"gen-{uid}")
    os.makedirs(gen_dir, exist_ok=True)
    save_text_to_file(gen_model.model, model_path)
    try:
        out_dir = generate(model_path, gen_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Generation error: {e}")
    frontend_dir = os.path.join(out_dir, "frontend")

    try:
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        build_dir = os.path.join(frontend_dir, "dist")
        base_url = f"/generated/gen-{uid}/frontend/dist/"
        inject_base_href(build_dir, base_url)
        background_tasks.add_task(cleanup_old_generations)
        return JSONResponse(content={"frontend_url": base_url}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


@app.post("/generate/file/preview", tags=["Preview"])
async def generate_preview_from_file(
    model_file: UploadFile = File(...),
    api_key: str = Security(get_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    uid = get_unique_id()
    model_path = os.path.join(TMP_DIR, f"model-{uid}.wdsl")
    gen_dir = os.path.join(TMP_DIR, f"gen-{uid}")
    os.makedirs(gen_dir, exist_ok=True)
    save_upload_file(model_file, model_path)
    try:
        out_dir = generate(model_path, gen_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Generation error: {e}")
    frontend_dir = os.path.join(out_dir, "frontend")
    try:
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        build_dir = os.path.join(frontend_dir, "dist")
        base_url = f"/generated/gen-{uid}/frontend/dist/"
        inject_base_href(build_dir, base_url)
        background_tasks.add_task(cleanup_old_generations)
        return JSONResponse(content={"frontend_url": base_url}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")
