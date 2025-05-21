import os
import re
import uuid
import base64
import tarfile
import time
import shutil
import traceback
import subprocess
import yaml

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
    Form,
)
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

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


def inject_base_href(build_dir: str, public_path_prefix: str) -> None:
    index_path = os.path.join(build_dir, "index.html")
    if not os.path.exists(index_path):
        print(f"Warning: index.html not found in {build_dir}. Cannot inject base href.")
        return

    with open(index_path, "r+", encoding="utf8") as f:
        content = f.read()
        original_content = content  # For debugging if needed

        # Ensure public_path_prefix is like /apps/uid/ (starts and ends with /)
        if not public_path_prefix.startswith("/"):
            public_path_prefix = "/" + public_path_prefix
        if not public_path_prefix.endswith("/"):
            public_path_prefix += "/"

        # --- 1. Inject <base href="..."> ---
        base_tag = f'<base href="{public_path_prefix}">'
        # Regex to find <head> and insert <base> as the first child
        # This handles <head> with attributes or newlines.
        head_pattern = re.compile(r"(<head[^>]*>)", re.IGNORECASE)
        match_head = head_pattern.search(content)
        if match_head:
            head_tag_full = match_head.group(1)
            # Check if base tag already exists to prevent duplicates
            if (
                f'<base href="{public_path_prefix}">' not in content
                and "<base " not in head_tag_full
            ):
                content = content.replace(
                    head_tag_full, f"{head_tag_full}\n    {base_tag}", 1
                )
        else:
            print(
                f"Warning: <head> tag not found in {index_path}. <base> tag not injected."
            )

        # --- 2. Inject window.__BASE_PATH__ ---
        js_base_path = public_path_prefix.rstrip("/")  # /apps/uid
        script_tag_content = f'window.__BASE_PATH__ = "{js_base_path}";'
        script_tag = f"<script>\n      {script_tag_content}\n    </script>"

        # Try to insert after <base> tag or early in <head>
        if base_tag in content:
            content = content.replace(base_tag, f"{base_tag}\n    {script_tag}", 1)
        elif match_head:  # If base tag wasn't inserted but head exists
            head_tag_full = match_head.group(1)  # Re-fetch in case content changed
            if script_tag_content not in content:  # Avoid duplicate script
                content = content.replace(
                    head_tag_full, f"{head_tag_full}\n    {script_tag}", 1
                )
        else:
            print(
                f"Warning: Could not determine where to inject window.__BASE_PATH__ in {index_path}."
            )

        # --- 3. Explicitly rewrite root-relative asset paths ---
        # This targets href="/..." or src="/..."
        # It will change src="/assets/file.js" to src="/apps/uid/assets/file.js"
        # It will change href="/favicon.ico" to href="/apps/uid/favicon.ico"

        # Path prefix without trailing slash for concatenation: /apps/uid
        prefix_no_slash = public_path_prefix.rstrip("/")

        def rewrite_path(match_obj):
            attribute_name = match_obj.group(1)  # src or href
            quote_char = match_obj.group(2)  # " or '
            original_path = match_obj.group(3)  # /assets/file.js or /favicon.ico

            # Check if path is root-relative (starts with /) AND
            # not already prefixed with public_path_prefix AND
            # not a data URI, mailto, tel, or full http(s) URL
            if (
                original_path.startswith("/")
                and not original_path.startswith(prefix_no_slash + "/")
                and not original_path.startswith(
                    ("data:", "mailto:", "tel:", "//", "http:", "https:")
                )
            ):
                # Prepend the prefix. original_path already starts with '/',
                # so prefix_no_slash + original_path works.
                # e.g., "/apps/uid" + "/assets/file.js" -> "/apps/uid/assets/file.js"
                new_path = f"{prefix_no_slash}{original_path}"
                return f"{attribute_name}={quote_char}{new_path}{quote_char}"
            else:
                # Return the original match if no rewrite is needed
                return match_obj.group(0)

        # Regex for src="..." and href="..." attributes with root-relative paths
        # It captures: 1=src|href, 2=quote, 3=path starting with /
        content = re.sub(r'(src|href)=(["\'])(/[^"\'>]+)\2', rewrite_path, content)

        # Also handle url(/...) in style attributes or <style> tags
        def rewrite_css_url_path(match_obj):
            quote_char = match_obj.group(1)  # " or ' or empty
            original_path = match_obj.group(2)  # /assets/image.png

            if (
                original_path.startswith("/")
                and not original_path.startswith(prefix_no_slash + "/")
                and not original_path.startswith(("data:", "//", "http:", "https:"))
            ):
                new_path = f"{prefix_no_slash}{original_path}"
                return f"url({quote_char}{new_path}{quote_char})"
            else:
                return match_obj.group(0)

        content = re.sub(
            r'url\((["\']?)(/[^"\'()]+)\1\)',  # Matches url('/path') or url(/path)
            rewrite_css_url_path,
            content,
        )

        if content == original_content:
            print(
                f"Warning: Content of {index_path} did not change after attempting to inject base href and rewrite paths."
            )
        else:
            print(f"Content of {index_path} was modified.")

        f.seek(0)
        f.write(content)
        f.truncate()

    print(f"Processed {index_path} with public path prefix '{public_path_prefix}'")


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


import yaml


def inject_traefik_labels_and_network(
    compose_path: str, uid: str, backend_internal_port: int = 8080
):  # Add backend_internal_port if it can vary
    with open(compose_path, "r") as f:
        compose_content = f.read()
        # Handle potential Jinja templating if it hasn't been rendered yet
        # For this example, we assume it's pure YAML after generation
        compose = yaml.safe_load(compose_content)

    public_path_for_container = f"/apps/{uid}/"  # This will be used by modify_html.sh
    # 0) Ensure the Traefik network 'proxy' is defined as external
    #    This means the 'proxy' network must already exist (created by Traefik's compose)
    compose["networks"] = {"traefik-demo": {"external": True}}

    for svc_name, svc_config in compose.get("services", {}).items():
        # 1) Remove any direct port bindings
        svc_config.pop("ports", None)

        # 2) Attach all services to the 'proxy' network for inter-service communication
        #    and for Traefik to discover the frontend.
        svc_config["networks"] = [
            "traefik-demo"
        ]  # Corrected: was a list of dicts, should be list of strings

        if svc_name == "frontend":
            # 3) Build labels list ONLY for the frontend
            labels = [
                "traefik.enable=true",
                # Route /apps/<uid>/* to this service
                f"traefik.http.routers.{uid}-frontend.rule=PathPrefix(`/apps/{uid}`)",
                f"traefik.http.routers.{uid}-frontend.entrypoints=web",  # Make sure this matches your Traefik entrypoint name
                # 4) Tell Traefik which internal port the frontend service listens on
                #    This must match EXPOSE in your frontend's Dockerfile (which is 80)
                f"traefik.http.services.{uid}-frontend.loadbalancer.server.port=80",
                # 5) (Optional but recommended) Strip the /apps/<uid> prefix
                f"traefik.http.middlewares.{uid}-frontend-stripprefix.stripprefix.prefixes=/apps/{uid}",  # Corrected middleware name
                f"traefik.http.routers.{uid}-frontend.middlewares={uid}-frontend-stripprefix",
            ]
            svc_config["labels"] = labels

            # ---- Add environment variable for the frontend service ----
            if "environment" not in svc_config or svc_config["environment"] is None:
                svc_config["environment"] = {}
            svc_config["environment"]["PUBLIC_PATH_PREFIX"] = public_path_for_container
        else:
            # For other services (e.g., backend), remove any existing labels
            # as we don't want to expose them directly via Traefik under the same path.
            # They will be accessible by the frontend service via their service name
            # on the 'proxy' network (e.g., http://backend:backend_internal_port)
            svc_config.pop("labels", None)

    # Write back out
    with open(compose_path, "w") as f:
        yaml.dump(compose, f, sort_keys=False)


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


# @app.get("/validate/base64", tags=["Validation"])
# async def validate_model_base64(fenc: str = "", api_key: str = Security(get_api_key)):
#     if not fenc:
#         raise HTTPException(status_code=404, detail="Empty base64 string")
#     uid = get_unique_id()
#     file_path = os.path.join(TMP_DIR, f"model_for_validation-{uid}.wdsl")
#     save_base64_to_file(fenc, file_path)
#     try:
#         build_model(file_path)
#         return {"status": 200, "message": "Model validation success"}
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=400, detail=f"Validation error: {e}")


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
    background_tasks.add_task(cleanup_old_generations)

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
    remote_compose_file = f"{remote_dir}/docker-compose.yml"
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

        # Edit the modify-html.js with the correct prefix
        modify_html_path = os.path.join(out_dir, "frontend", "modify-html.js")
        with open(modify_html_path, "r+", encoding="utf8") as f:
            content = f.read()
            updated = content.replace(
                'const prefix = ""; // this is updated after generation',
                f'const prefix = "/apps/{uid}/";',
            )
            f.seek(0)
            f.write(updated)
            f.truncate()

        # Inject traefik labels into docker-compose.yml
        compose_path = os.path.join(out_dir, "docker-compose.yml")
        inject_traefik_labels_and_network(compose_path, uid)

        # Copy the generated files to the vm
        subprocess.run(
            ["scp", "-r", gen_dir, f"{VM_MACHINE_USER}@{VM_MACHINE_IP}:{remote_dir}"],
            check=True,
        )

        # Deploy the app using docker-compose
        subprocess.run(
            [
                "ssh",
                f"{VM_MACHINE_USER}@{VM_MACHINE_IP}",
                f"cd /tmp/webapp-{uid} && docker compose up -d",
            ],
            check=True,
        )

        return {"message": "Deployed", "url": f"http://192.168.1.9/apps/{uid}"}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deployment failed: {e}")


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
