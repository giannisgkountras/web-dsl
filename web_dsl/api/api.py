import os
import traceback
import subprocess

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    UploadFile,
    status,
    HTTPException,
    BackgroundTasks,
    File,
    Security,
    Body,
    Form,
)
from typing import List
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from .utils import (
    cleanup_old_generations,
    get_unique_id,
    make_tarball,
    save_text_to_file,
    save_upload_file,
    postprocess_generation_for_deployment,
)
from web_dsl.language import build_model
from web_dsl.generate import generate
from web_dsl.m2m.openapi_to_webdsl import transform_openapi_to_webdsl
from web_dsl.m2m.goaldsl_to_webdsl import transform_goaldsl_to_webdsl
from web_dsl.m2m.asyncapi_to_webdsl import transform_asyncapi_to_webdsl

# Load the .env file
load_dotenv()

API_KEY = os.getenv("API_KEY", "API_KEY")
VM_MACHINE_IP = os.getenv("VM_MACHINE_IP", "")
VM_MACHINE_USER = os.getenv("VM_MACHINE_USER", "")
VM_MACHINE_SSH_PORT = os.getenv("VM_MACHINE_SSH_PORT", "22")
TMP_DIR = "./tmp/"
CLEANUP_THRESHOLD = 60 * 15  # 15m in seconds
SSH_KEY_PATH = "/root/.ssh/id_rsa"  # Path to the private key in the container

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


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
    )


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
        traceback.print_exc()
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


@app.post("/generate/file", tags=["Generation"])
async def generate_from_files(
    model_files: List[UploadFile] = File(...),
    main_filename: str = Form(None),  # Optional
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: str = Security(get_api_key),
):
    uid = get_unique_id()
    model_dir = os.path.join(TMP_DIR, f"models-{uid}")
    gen_dir = os.path.join(TMP_DIR, f"gen-{uid}")
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(gen_dir, exist_ok=True)
    background_tasks.add_task(cleanup_old_generations, TMP_DIR, CLEANUP_THRESHOLD)

    model_paths = {}

    try:
        # Save files and keep track of names
        for model_file in model_files:
            dest_path = os.path.join(model_dir, model_file.filename)
            save_upload_file(model_file, dest_path)
            model_paths[model_file.filename] = dest_path

        # Determine the main file
        if len(model_files) == 1:
            main_model_path = next(iter(model_paths.values()))
        elif main_filename and main_filename in model_paths:
            main_model_path = model_paths[main_filename]
        else:
            raise HTTPException(
                status_code=400, detail="Main file not specified or not found."
            )

        out_dir = generate(main_model_path, gen_dir)

        tarball_path = os.path.join(TMP_DIR, f"{uid}.tar.gz")
        make_tarball(tarball_path, out_dir)

        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Transformation error: {e}")


@app.post("/deploy", tags=["Deployment"])
async def generate_and_deploy(
    model_files: List[UploadFile] = File(...),
    main_filename: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: str = Security(get_api_key),
):
    uid = get_unique_id()
    model_dir = os.path.join(TMP_DIR, f"models-{uid}")
    gen_dir = f"./tmp/gen-{uid}"
    remote_dir = f"/tmp/webapp-{uid}"
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(gen_dir, exist_ok=True)

    model_paths = {}

    # Save files and keep track of names
    for model_file in model_files:
        dest_path = os.path.join(model_dir, model_file.filename)
        save_upload_file(model_file, dest_path)
        model_paths[model_file.filename] = dest_path

    # Determine main file
    if len(model_files) == 1:
        main_model_path = next(iter(model_paths.values()))
    elif main_filename and main_filename in model_paths:
        main_model_path = model_paths[main_filename]
    else:
        raise HTTPException(status_code=400, detail="Main file not specified.")

    try:
        # Generate app
        out_dir = generate(main_model_path, gen_dir)

        username, password = postprocess_generation_for_deployment(
            generation_dir=out_dir,
            uid=uid,
            VM_MACHINE_IP=VM_MACHINE_IP,
            VM_MACHINE_USER=VM_MACHINE_USER,
        )

        print(f"Generated app with username: {username}, password: {password}")

        # Copy the postprocessed generated files to the vm
        scp_command = [
            "scp",
            "-P",
            str(VM_MACHINE_SSH_PORT),
            "-o",
            "StrictHostKeyChecking=no",  # Skip host key check
            "-o",
            "UserKnownHostsFile=/dev/null",  # Don't update known_hosts
            "-o",
            "BatchMode=yes",  # Never ask for passwords, fail if keys don't work
            "-i",
            SSH_KEY_PATH,  # Explicitly use the private key
            "-r",  # Recursive for directory
            gen_dir,  # Source
            f"{VM_MACHINE_USER}@{VM_MACHINE_IP}:{remote_dir}",  # Destination
        ]
        scp_result = subprocess.run(
            scp_command, check=False, capture_output=True, text=True, timeout=120
        )
        if scp_result.returncode != 0:
            print(f"[{uid}] SCP failed! Exit code: {scp_result.returncode}")
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed: SCP error.",
            )
        print(f"[{uid}] SCP successful.")

        remote_command = f"cd {remote_dir} && docker compose up --build -d"
        ssh_command = [
            "ssh",
            "-p",
            str(VM_MACHINE_SSH_PORT),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "BatchMode=yes",
            "-i",
            SSH_KEY_PATH,
            f"{VM_MACHINE_USER}@{VM_MACHINE_IP}",  # Target host
            remote_command,  # Command to execute
        ]
        # Deploy the app using docker-compose
        ssh_result = subprocess.run(
            ssh_command, check=False, capture_output=True, text=True, timeout=300
        )

        if ssh_result.returncode != 0:
            print(
                f"[{uid}] Remote SSH command failed! Exit code: {ssh_result.returncode}"
            )

            raise HTTPException(
                status_code=500, detail=f"Deployment failed: Remote execution error."
            )
        print(f"[{uid}] Remote SSH command successful.")
        return {
            "message": "Deployed",
            "url": f"http://{VM_MACHINE_IP}/apps/{uid}/",
            "username": username,
            "password": password,
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deployment failed")


# ============= Transformations Endpoint =============
@app.post("/transform/openapi", tags=["Transformations"])
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


# ============= Transformations Endpoint =============
@app.post("/transform/goaldsl", tags=["Transformations"])
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


@app.post("/transform/asyncapi", tags=["Transformations"])
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
