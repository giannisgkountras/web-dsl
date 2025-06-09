import os
import traceback
from typing import List
from ..config import get_api_key, TMP_DIR, CLEANUP_THRESHOLD
from fastapi import (
    APIRouter,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    File,
    Security,
    Body,
    Form,
)
from fastapi.responses import FileResponse
from ..utils import (
    cleanup_old_generations,
    get_unique_id,
    make_tarball,
    save_text_to_file,
    save_upload_file,
)
from ..models import TransformationModel
from web_dsl.generate import generate

router = APIRouter(tags=["Generation"])


@router.post("/generate", status_code=201)
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


@router.post("/generate/file", status_code=201)
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
