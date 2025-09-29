import os
import io
import traceback
import subprocess
from typing import List, Optional
from fastapi import (
    UploadFile,
    HTTPException,
    BackgroundTasks,
    File,
    Security,
    Form,
    Depends,
    APIRouter,
    Path,
    Body,
)
from fastapi.concurrency import run_in_threadpool
import aiosqlite

from ..utils import (
    get_unique_id,
    save_upload_file,
    postprocess_generation_for_deployment,
    run_remote_ssh_command_capture,
    generate_credentials,
    CapturedSSHResult,
)
from ..database import (
    get_db_connection,
    db_create_deployment_record,
    db_update_deployment_status,
    db_get_deployment_by_uid,
    db_get_deployments_by_user_id,
    db_get_public_deployments,
    db_get_all_deployments,
)
from web_dsl.generate import generate
from ..config import (
    get_api_key,
    TMP_DIR,
    VM_MACHINE_IP,
    VM_MACHINE_USER,
    VM_MACHINE_SSH_PORT,
    SSH_KEY_PATH,
)
from ..models import (
    DeploymentDetailResponse,
    UserIDBody,  # May not be needed if user_id is in path or query
    # DeploymentActionBody,  # May not be needed if deployment_uid is in path
    DockerStatsResponse,
    format_deployment_response,
    DeploymentStringModel
    # DeploymentCreateBody,  # New model for creation
    # StartDeploymentBody,  # New model for start action requiring user_id
)

router = APIRouter(prefix="/deploy")

async def run_deployment(
    conn: aiosqlite.Connection,
    uid: str,
    model_str: str,
    model_dir_local: str,
    gen_dir_local: str,
    remote_dir_vm: str,
    docker_project_name: str,
    is_public: bool,
    app_username: str,
    app_password: str,
):
    """
    This function contains the long-running deployment logic and will be run as a background task.
    """
    try:
        main_model_path = os.path.join(model_dir_local, f"model-{uid}.wdsl")

        with open(main_model_path, "w", encoding="utf-8") as f:
            f.write(model_str)

        generated_app_path = await run_in_threadpool(
            generate, main_model_path, gen_dir_local
        )

        await run_in_threadpool(
            postprocess_generation_for_deployment,
            generation_dir=generated_app_path,
            uid=uid,
            VM_MACHINE_IP=VM_MACHINE_IP,
            VM_MACHINE_USER=VM_MACHINE_USER,
            username=app_username,
            password=app_password,
            public_deployment=is_public,
        )

        mkdir_result: CapturedSSHResult = await run_in_threadpool(
            run_remote_ssh_command_capture, f"mkdir -p {remote_dir_vm}"
        )
        if mkdir_result.returncode != 0:
            err_msg = f"Mkdir fail. Code:{mkdir_result.returncode}. Err:{mkdir_result.stderr}"
            await db_update_deployment_status(conn, uid, "failed", error_message=err_msg)
            return

        scp_cmd_list = [
            "scp", "-P", str(VM_MACHINE_SSH_PORT),
            "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "BatchMode=yes", "-o", "LogLevel=ERROR",
            "-i", SSH_KEY_PATH, "-r",
            f"{generated_app_path}/.", f"{VM_MACHINE_USER}@{VM_MACHINE_IP}:{remote_dir_vm}/",
        ]
        scp_res = await run_in_threadpool(
            subprocess.run, scp_cmd_list, check=False,
            capture_output=True, text=True, timeout=120,
        )
        if scp_res.returncode != 0:
            err_msg = f"SCP fail. Code:{scp_res.returncode}. Err:{scp_res.stderr}"
            await db_update_deployment_status(conn, uid, "failed", error_message=err_msg)
            return

        deploy_cmd = f"cd {remote_dir_vm} && docker compose -p {docker_project_name} up --build -d"
        ssh_deploy_res: CapturedSSHResult = await run_in_threadpool(
            run_remote_ssh_command_capture, deploy_cmd, timeout=300
        )

        if ssh_deploy_res.returncode != 0:
            logs_cmd = f"cd {remote_dir_vm} && docker compose -p {docker_project_name} logs --tail=50"
            logs_res: CapturedSSHResult = await run_in_threadpool(
                run_remote_ssh_command_capture, logs_cmd, timeout=30
            )
            err_detail = (
                f"Compose fail! Code:{ssh_deploy_res.returncode}. Err:{ssh_deploy_res.stderr}. "
                f"Out:{ssh_deploy_res.stdout}. Logs:{logs_res.stdout} {logs_res.stderr}"
            )
            await db_update_deployment_status(conn, uid, "failed", error_message=err_detail)
            return

        dep_url = f"http://{VM_MACHINE_IP}/apps/{uid}/"
        await db_update_deployment_status(
            conn, uid, "running", url=dep_url,
            app_username=app_username, app_password=app_password,
        )

    except Exception as e:
        traceback.print_exc()
        err_msg = f"Deploy fail in background: {str(e)}"
        await db_update_deployment_status(conn, uid, "failed", error_message=err_msg)


@router.post(
    "",
    status_code=202,  # Use 202 Accepted for background tasks
    tags=["Deployments - Lifecycle"],
)
async def create_new_deployment(
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
    deployment: DeploymentStringModel = Body(...),
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    uid = get_unique_id()
    model_dir_local = os.path.join(TMP_DIR, f"models-{uid}")
    gen_dir_local = os.path.join(TMP_DIR, f"gen-{uid}")
    remote_dir_vm = f"/tmp/webapp-{uid}"
    docker_project_name = f"webapp-{uid}"
    is_public = deployment.is_public

    await run_in_threadpool(os.makedirs, model_dir_local, exist_ok=True)
    await run_in_threadpool(os.makedirs, gen_dir_local, exist_ok=True)

    # 1. Generate credentials immediately
    app_username, app_password = generate_credentials(public=is_public)

    # 2. Create the initial database record with a "pending" status
    await db_create_deployment_record(
        conn=conn,
        deployment_uid=uid,
        user_id=deployment.user_id,
        is_public=is_public,
        model_dir_local=model_dir_local,
        gen_dir_local=gen_dir_local,
        remote_dir_vm=remote_dir_vm,
        docker_project_name=docker_project_name,
    )

    # 3. Add the long-running deployment process as a background task
    background_tasks.add_task(
        run_deployment,
        conn=conn,
        uid=uid,
        model_str=deployment.model_str,
        model_dir_local=model_dir_local,
        gen_dir_local=gen_dir_local,
        remote_dir_vm=remote_dir_vm,
        docker_project_name=docker_project_name,
        is_public=is_public,
        app_username=app_username,
        app_password=app_password,
    )

    # 4. Immediately return the response to the client
    return {
        "deployment_uid": uid,
        "status": "pending",
        "username": app_username,
        "password": app_password,
        "url": f"http://{VM_MACHINE_IP}/apps/{uid}/",
        "message": "Deployment has been initiated and is running in the background.",
    }

@router.post(
    "/file",
    status_code=201,
    tags=["Deployments - Lifecycle"],
)
async def create_new_deployment_file(
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
    user_id: str = Form(...),
    is_public: bool = Form(False),
    model_files: List[UploadFile] = File(...),
    main_filename: Optional[str] = Form(None),
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    uid = get_unique_id()
    model_dir_local = os.path.join(TMP_DIR, f"models-{uid}")
    gen_dir_local = os.path.join(TMP_DIR, f"gen-{uid}")
    remote_dir_vm = f"/tmp/webapp-{uid}"
    docker_project_name = f"webapp-{uid}"

    await run_in_threadpool(os.makedirs, model_dir_local, exist_ok=True)
    await run_in_threadpool(os.makedirs, gen_dir_local, exist_ok=True)

    await db_create_deployment_record(
        conn,
        uid,
        user_id,
        is_public,
        model_dir_local,
        gen_dir_local,
        remote_dir_vm,
        docker_project_name,
    )

    model_paths = {}
    for model_file in model_files:
        dest_path = os.path.join(model_dir_local, model_file.filename)
        await run_in_threadpool(save_upload_file, model_file, dest_path)
        model_paths[model_file.filename] = dest_path

    if len(model_files) == 1 and not main_filename:
        main_model_path = next(iter(model_paths.values()))
    elif main_filename and main_filename in model_paths:
        main_model_path = model_paths[main_filename]
    else:
        await db_update_deployment_status(
            conn, uid, "failed", error_message="Main file not specified or ambiguous."
        )
        raise HTTPException(
            status_code=400, detail="Main file not specified or ambiguous."
        )

    try:
        generated_app_path = await run_in_threadpool(
            generate, main_model_path, gen_dir_local
        )
        app_username, app_password = await run_in_threadpool(
            postprocess_generation_for_deployment,
            generation_dir=generated_app_path,
            uid=uid,
            VM_MACHINE_IP=VM_MACHINE_IP,
            VM_MACHINE_USER=VM_MACHINE_USER,
            public_deployment=is_public,
        )

        mkdir_result: CapturedSSHResult = await run_in_threadpool(
            run_remote_ssh_command_capture, f"mkdir -p {remote_dir_vm}"
        )
        if mkdir_result.returncode != 0:
            err_msg = (
                f"Mkdir fail. Code:{mkdir_result.returncode}. Err:{mkdir_result.stderr}"
            )
            await db_update_deployment_status(
                conn, uid, "failed", error_message=err_msg
            )
            raise HTTPException(
                status_code=500, detail=f"Deploy fail: SCP setup. {err_msg}"
            )

        scp_cmd_list = [
            "scp",
            "-P",
            str(VM_MACHINE_SSH_PORT),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "BatchMode=yes",
            "-o",
            "LogLevel=ERROR",
            "-i",
            SSH_KEY_PATH,
            "-r",
            f"{generated_app_path}/.",
            f"{VM_MACHINE_USER}@{VM_MACHINE_IP}:{remote_dir_vm}/",
        ]
        scp_res = await run_in_threadpool(
            subprocess.run,
            scp_cmd_list,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if scp_res.returncode != 0:
            err_msg = f"SCP fail. Code:{scp_res.returncode}. Err:{scp_res.stderr}"
            await db_update_deployment_status(
                conn, uid, "failed", error_message=err_msg
            )
            raise HTTPException(status_code=500, detail=f"Deploy fail: SCP. {err_msg}")

        deploy_cmd = f"cd {remote_dir_vm} && docker compose -p {docker_project_name} up --build -d"
        ssh_deploy_res: CapturedSSHResult = await run_in_threadpool(
            run_remote_ssh_command_capture, deploy_cmd, timeout=300
        )

        if ssh_deploy_res.returncode != 0:
            logs_cmd = f"cd {remote_dir_vm} && docker compose -p {docker_project_name} logs --tail=50"
            logs_res: CapturedSSHResult = await run_in_threadpool(
                run_remote_ssh_command_capture, logs_cmd, timeout=30
            )
            err_detail = (
                f"Compose fail! Code:{ssh_deploy_res.returncode}. Err:{ssh_deploy_res.stderr}. "
                f"Out:{ssh_deploy_res.stdout}. Logs:{logs_res.stdout} {logs_res.stderr}"
            )
            await db_update_deployment_status(
                conn, uid, "failed", error_message=err_detail
            )
            raise HTTPException(
                status_code=500, detail=f"Deploy fail: Remote exec. {err_detail}"
            )

        dep_url = f"http://{VM_MACHINE_IP}/apps/{uid}/"
        await db_update_deployment_status(
            conn,
            uid,
            "running",
            url=dep_url,
            app_username=app_username,
            app_password=app_password,
        )

        # Return the full deployment details
        created_deployment = await db_get_deployment_by_uid(conn, uid)
        # background_tasks.add_task(cleanup_local_dirs, [model_dir_local, gen_dir_local])
        return {
            "id": created_deployment["id"],
            "deployment_uid": created_deployment["deployment_uid"],
            "status": created_deployment["status"],
            "username": created_deployment["app_username"],
            "password": created_deployment["app_password"],
            "url": created_deployment["url"],
            "created_at": created_deployment["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        err_msg = f"Deploy fail: {str(e)}"
        await db_update_deployment_status(conn, uid, "failed", error_message=err_msg)
        raise HTTPException(status_code=500, detail=err_msg)


@router.get(
    "", response_model=List[DeploymentDetailResponse], tags=["Deployments - Listing"]
)
async def list_all_deployments_endpoint(
    api_key: str = Security(get_api_key),  # Admin/privileged access
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    deployments_rows = await db_get_all_deployments(conn)  # Needs this DB function
    return [format_deployment_response(row) for row in deployments_rows if row]


@router.get(
    "/user/{user_id}",
    response_model=List[DeploymentDetailResponse],
    tags=["Deployments - Listing"],
)
async def list_user_deployments_endpoint(
    user_id: str = Path(
        ..., description="The ID of the user whose deployments to list"
    ),
    api_key: str = Security(
        get_api_key
    ),  # Auth check: is requester allowed to see this user_id's deployments?
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    deployments_rows = await db_get_deployments_by_user_id(conn, user_id)
    return [format_deployment_response(row) for row in deployments_rows if row]


@router.get(
    "/public",
    response_model=List[DeploymentDetailResponse],
    tags=["Deployments - Listing"],
)
async def list_public_deployments_endpoint(  # No API key needed if truly public
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    deployments_rows = await db_get_public_deployments(conn)
    return [format_deployment_response(row) for row in deployments_rows if row]


@router.get(
    "/{deployment_uid}",
    response_model=DeploymentDetailResponse,
    tags=["Deployments - Listing"],
)
async def get_single_deployment_details(
    deployment_uid: str = Path(..., description="The UID of the deployment"),
    user_id_query: Optional[str] = Body(
        None, description="User ID for authorization check, if required by policy"
    ),  # If not admin, user must own
    api_key: str = Security(get_api_key),
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    deployment_row = await db_get_deployment_by_uid(conn, deployment_uid)
    if not deployment_row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    # Add authorization logic: e.g., if not admin, user_id_query must match deployment_row["user_id"]
    # For now, assuming API key implies sufficient access or it's a public deployment.
    # if user_id_query and deployment_row["user_id"] != user_id_query:
    #     raise HTTPException(status_code=403, detail="User not authorized to view this deployment's details.")
    return format_deployment_response(deployment_row)


async def _perform_kill_logic(
    deployment_uid: str, requesting_user_id: str, conn: aiosqlite.Connection
):
    deployment = await db_get_deployment_by_uid(conn, deployment_uid)
    if not deployment:
        raise HTTPException(
            status_code=404, detail=f"Deployment {deployment_uid} not found."
        )
    if deployment["user_id"] != requesting_user_id:
        raise HTTPException(status_code=403, detail="User not authorized to kill.")
    if deployment["status"] == "killed":
        return f"Deployment {deployment_uid} already killed."
    if not deployment["docker_project_name"] or not deployment["remote_dir_vm"]:
        await db_update_deployment_status(
            conn, deployment_uid, "killed", error_message="Kill: Missing Docker info."
        )
        raise HTTPException(
            status_code=500, detail="Deployment info incomplete for kill op."
        )

    project_name, remote_dir_vm = (
        deployment["docker_project_name"],
        deployment["remote_dir_vm"],
    )
    kill_cmd = f"docker compose -p {project_name} down --remove-orphans -v"
    cleanup_cmd = f"rm -rf {remote_dir_vm}"
    kill_success, errors = False, []

    kill_res: CapturedSSHResult = await run_in_threadpool(
        run_remote_ssh_command_capture, kill_cmd, timeout=180
    )
    if kill_res.returncode == 0:
        kill_success = True
    else:
        errors.append(
            f"Docker down error (Code:{kill_res.returncode}): {kill_res.stderr or kill_res.stdout}"
        )

    cleanup_res: CapturedSSHResult = await run_in_threadpool(
        run_remote_ssh_command_capture, cleanup_cmd, timeout=60
    )
    if cleanup_res.returncode != 0:
        errors.append(
            f"Dir cleanup error (Code:{cleanup_res.returncode}): {cleanup_res.stderr or cleanup_res.stdout}"
        )

    if kill_success:
        msg = "Killed successfully." + (
            f" Cleanup issues: {'; '.join(errors)}" if errors else ""
        )
        await db_update_deployment_status(
            conn, deployment_uid, "killed", error_message=msg if errors else None
        )
        return f"Deployment {deployment_uid} {msg}"
    else:
        err_summary = f"Failed to stop/remove. Errors: {'; '.join(errors)}"
        await db_update_deployment_status(
            conn, deployment_uid, "kill_failed", error_message=err_summary
        )
        raise HTTPException(
            status_code=500,
            detail=f"Deployment {deployment_uid} kill op failed. {err_summary}",
        )


@router.post(
    "/{deployment_uid}/kill",
    summary="Kill a specific deployment",
    tags=["Deployments - Lifecycle"],
)
async def kill_single_deployment(
    deployment_uid: str = Path(..., description="The UID of the deployment to kill"),
    body: UserIDBody = Body(...),  # Contains requesting_user_id
    api_key: str = Security(get_api_key),
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    message = await _perform_kill_logic(deployment_uid, body.user_id, conn)
    return {"message": message, "deployment_uid": deployment_uid}


@router.post(
    "/user/{user_id}/kill_all",
    summary="Kill all deployments for a user",
    tags=["Deployments - Lifecycle"],
)
async def kill_all_user_deployments(
    user_id: str = Path(
        ..., description="The ID of the user whose deployments to kill"
    ),
    api_key: str = Security(get_api_key),  # Requires privileged access
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    user_deployments = await db_get_deployments_by_user_id(conn, user_id)
    if not user_deployments:
        return {"message": f"No deployments for user {user_id}."}
    results = []
    for dep_row in user_deployments:
        dep_uid = dep_row["deployment_uid"]
        if dep_row["status"] == "killed":
            results.append(
                {
                    "deployment_uid": dep_uid,
                    "status": "skipped",
                    "detail": "Already killed.",
                }
            )
            continue
        try:
            message = await _perform_kill_logic(
                dep_uid, user_id, conn
            )  # user_id is the owner
            results.append(
                {"deployment_uid": dep_uid, "status": "success", "detail": message}
            )
        except HTTPException as e:
            results.append(
                {"deployment_uid": dep_uid, "status": "failed", "detail": e.detail}
            )
        except Exception as e:
            traceback.print_exc()
            results.append(
                {"deployment_uid": dep_uid, "status": "error", "detail": str(e)}
            )
    return {"message": f"Kill all for user {user_id} processed.", "results": results}


async def _perform_start_logic(
    deployment_uid: str, requesting_user_id: str, conn: aiosqlite.Connection
):
    deployment = await db_get_deployment_by_uid(conn, deployment_uid)
    if not deployment:
        raise HTTPException(
            status_code=404, detail=f"Deployment {deployment_uid} not found."
        )
    if deployment["user_id"] != requesting_user_id:
        raise HTTPException(status_code=403, detail="User not authorized to start.")
    if deployment["status"] == "running":
        return f"Deployment {deployment_uid} is already running."
    if deployment["status"] == "failed" and not (
        deployment["remote_dir_vm"] and deployment["docker_project_name"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Cannot start: deployment was failed and lacks remote info for restart.",
        )
    if not deployment["remote_dir_vm"] or not deployment["docker_project_name"]:
        raise HTTPException(
            status_code=500, detail="Deployment info incomplete, cannot perform start."
        )

    remote_dir_vm, docker_project_name = (
        deployment["remote_dir_vm"],
        deployment["docker_project_name"],
    )
    start_cmd = f"cd {remote_dir_vm} && docker compose -p {docker_project_name} up --build -d"  # Rebuild on start

    ssh_start_res: CapturedSSHResult = await run_in_threadpool(
        run_remote_ssh_command_capture, start_cmd, timeout=300
    )
    if ssh_start_res.returncode == 0:
        await db_update_deployment_status(
            conn, deployment_uid, "running"
        )  # Update status, URL etc. should persist
        return f"Deployment {deployment_uid} started successfully."
    else:
        logs_cmd = f"cd {remote_dir_vm} && docker compose -p {docker_project_name} logs --tail=50"
        logs_res: CapturedSSHResult = await run_in_threadpool(
            run_remote_ssh_command_capture, logs_cmd, timeout=30
        )
        err_detail = (
            f"Start fail! Code:{ssh_start_res.returncode}. Err:{ssh_start_res.stderr}. "
            f"Out:{ssh_start_res.stdout}. Logs:{logs_res.stdout} {logs_res.stderr}"
        )
        await db_update_deployment_status(
            conn, deployment_uid, "start_failed", error_message=err_detail
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to start {deployment_uid}. {err_detail}"
        )


@router.post(
    "/{deployment_uid}/start",
    summary="Start a specific (previously killed/stopped) deployment",
    tags=["Deployments - Lifecycle"],
)
async def start_single_deployment(
    deployment_uid: str = Path(..., description="The UID of the deployment to start"),
    body: UserIDBody = Body(...),  # Contains requesting_user_id
    api_key: str = Security(get_api_key),
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    message = await _perform_start_logic(deployment_uid, body.user_id, conn)
    return {"message": message, "deployment_uid": deployment_uid}


@router.get(
    "/{deployment_uid}/stats",
    response_model=Optional[DockerStatsResponse],
    tags=["Deployments - Listing"],
)
async def get_single_deployment_stats(
    deployment_uid: str = Path(..., description="The UID of the deployment"),
    user_id_query: Optional[str] = Body(
        None, description="User ID for authorization check, if required"
    ),  # If not admin, user must own
    api_key: str = Security(get_api_key),
    conn: aiosqlite.Connection = Depends(get_db_connection),
):
    deployment = await db_get_deployment_by_uid(conn, deployment_uid)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    # Add more robust auth logic here based on user_id_query vs deployment owner vs admin
    if user_id_query and deployment["user_id"] != user_id_query:
        raise HTTPException(
            status_code=403, detail="User not authorized for these stats."
        )
    if deployment["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Deployment not running (status: {deployment['status']}).",
        )
    if not deployment["docker_project_name"]:
        raise HTTPException(status_code=500, detail="Deployment metadata incomplete.")

    project_name = deployment["docker_project_name"]
    ids_cmd = f"docker compose -p {project_name} ps -q"
    ps_res: CapturedSSHResult = await run_in_threadpool(
        run_remote_ssh_command_capture, ids_cmd
    )
    if ps_res.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"No containers. Code:{ps_res.returncode}. Err:{ps_res.stderr or ps_res.stdout}",
        )
    if not ps_res.stdout.strip():
        raise HTTPException(
            status_code=404, detail=f"No active containers for {project_name}."
        )

    container_ids = ps_res.stdout.strip().split("\n")
    if not container_ids or not container_ids[0]:
        raise HTTPException(
            status_code=404, detail=f"No container IDs for {project_name}."
        )
    target_id = container_ids[0]

    stats_fmt = "{{.ID}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}"
    stats_cmd = f'docker stats --no-stream --format "{stats_fmt}" {target_id}'
    stats_res: CapturedSSHResult = await run_in_threadpool(
        run_remote_ssh_command_capture, stats_cmd
    )

    if stats_res.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Stats fail. Code:{stats_res.returncode}. Err:{stats_res.stderr or stats_res.stdout}",
        )
    raw = stats_res.stdout.strip()
    if not raw:
        raise HTTPException(status_code=500, detail=f"Empty stats for {target_id}.")

    parts = raw.split(",")
    if len(parts) != 7:
        raise HTTPException(
            status_code=500, detail=f"Bad stats format ({len(parts)} parts): '{raw}'"
        )
    mem_full = parts[2].split("/")
    return DockerStatsResponse(
        container_id=parts[0],
        cpu_percent=parts[1],
        memory_usage=mem_full[0].strip(),
        memory_limit=mem_full[1].strip() if len(mem_full) > 1 else "N/A",
        memory_percent=parts[3],
        net_io=parts[4],
        block_io=parts[5],
        pids=parts[6],
        raw_output=raw,
    )
