import yaml
import time
import os
import shutil
import uuid
import base64
import tarfile
import re
import secrets
import subprocess
import json
from fastapi import UploadFile
from .config import VM_MACHINE_IP, VM_MACHINE_USER, VM_MACHINE_SSH_PORT, SSH_KEY_PATH
from .models import CapturedSSHResult
from typing import List


def inject_traefik_labels_and_network(
    compose_path: str,
    uid: str,
    username: str = "admin",
    password: str = None,
    backend_api_internal_port: int = 7070,
    backend_ws_internal_port: int = 8765,
    frontend_internal_port: int = 80,
    public: bool = False,
):

    if not public and password:
        # Call htpasswd -nb to generate the hash
        result = subprocess.run(
            ["htpasswd", "-nb", username, password],
            capture_output=True,
            text=True,
            check=True,
        )
        hashed_result = result.stdout.strip()
        escaped_hashed_result = hashed_result.replace("$", "$$")
    else:
        escaped_hashed_result = None

    with open(compose_path, "r") as f:
        compose_content = f.read()
        compose = yaml.safe_load(compose_content)

    auth_middleware_name = f"{uid}-auth"
    ws_strip_prefix_middleware_name = f"{uid}-ws-stripprefix"
    # --- Define Router and Service Names ---
    frontend_router_name = f"{uid}-frontend"
    frontend_service_name = f"{uid}-frontend-svc"

    api_router_name = f"{uid}-backend-api"
    api_service_name = f"{uid}-backend-api-svc"

    ws_router_name = f"{uid}-backend-ws"
    ws_service_name = f"{uid}-backend-ws-svc"

    api_full_path_prefix = f"/apps/{uid}/api/"
    ws_full_path_prefix = f"/apps/{uid}/ws/"
    app_base_path_prefix = f"/apps/{uid}/"

    compose["networks"] = {"traefik-demo": {"external": True}}

    for svc_name, svc_config in compose.get("services", {}).items():
        # Remove any direct port bindings
        svc_config.pop("ports", None)

        # Attach all services to the 'proxy' network for inter-service communication
        #    and for Traefik to discover the frontend.
        svc_config["networks"] = ["traefik-demo"]

        if svc_name == "frontend":
            labels = [
                "traefik.enable=true",
                # --- Frontend Router ---
                # Rule: Matches /apps/{uid}/ but NOT /apps/{uid}/api/ AND NOT /apps/{uid}/ws/
                f"traefik.http.routers.{frontend_router_name}.rule=PathPrefix(`{app_base_path_prefix}`) && !PathPrefix(`{api_full_path_prefix}`) && !PathPrefix(`{ws_full_path_prefix}`)",
                f"traefik.http.routers.{frontend_router_name}.entrypoints=web",
                f"traefik.http.routers.{frontend_router_name}.priority=10",  # Lower priority for general path
                f"traefik.http.routers.{frontend_router_name}.service={frontend_service_name}",
                # --- Frontend Service ---
                f"traefik.http.services.{frontend_service_name}.loadbalancer.server.port={frontend_internal_port}",
            ]

            if not public:

                # If not public add auth middleware
                labels.extend(
                    [
                        # --- Authentication Middleware Definition ---
                        f"traefik.http.middlewares.{auth_middleware_name}.basicauth.users={escaped_hashed_result}",
                        # Apply auth middleware to the frontend router
                        f"traefik.http.routers.{frontend_router_name}.middlewares={auth_middleware_name}",
                    ]
                )
            svc_config["labels"] = labels

        elif svc_name == "backend":
            labels = [
                "traefik.enable=true",
                # --- API Router ---
                f"traefik.http.routers.{api_router_name}.rule=PathPrefix(`{api_full_path_prefix}`)",
                f"traefik.http.routers.{api_router_name}.priority=20",
                f"traefik.http.routers.{api_router_name}.entrypoints=web",
                f"traefik.http.routers.{api_router_name}.service={api_service_name}",
                # --- API Service ---
                f"traefik.http.services.{api_service_name}.loadbalancer.server.port={backend_api_internal_port}",
                # --- WebSocket Router ---
                f"traefik.http.routers.{ws_router_name}.rule=PathPrefix(`{ws_full_path_prefix}`)",
                f"traefik.http.routers.{ws_router_name}.priority=25",  # Highest priority
                f"traefik.http.routers.{ws_router_name}.entrypoints=web",
                f"traefik.http.routers.{ws_router_name}.service={ws_service_name}",
                # --- WebSocket Service ---
                f"traefik.http.services.{ws_service_name}.loadbalancer.server.port={backend_ws_internal_port}",
                # --- WebSocket Middlewares Definition & Application ---
                # 1. Define StripPrefix middleware for WS
                f"traefik.http.middlewares.{ws_strip_prefix_middleware_name}.stripprefix.prefixes={ws_full_path_prefix}",
            ]
            if not public:
                # Add auth for not public deployments
                labels.extend(
                    [
                        f"traefik.http.routers.{api_router_name}.middlewares={auth_middleware_name}",
                        f"traefik.http.routers.{ws_router_name}.middlewares={auth_middleware_name},{ws_strip_prefix_middleware_name}",
                    ]
                )
            # Traefik labels for Backend API
            svc_config["labels"] = labels
        else:
            svc_config.pop("labels", None)

    # Write back out
    with open(compose_path, "w") as f:
        yaml.dump(compose, f, sort_keys=False)

def generate_credentials(public: bool = False):
    """
    Generates a username and password if the deployment is not public.
    """
    username = "admin"
    password = None
    if not public:
        password = secrets.token_urlsafe(16)
    return username, password


def cleanup_old_generations(TMP_DIR, CLEANUP_THRESHOLD):
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


def _run_ssh_command_base(command_parts, timeout):
    base_ssh_args = [
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
    ]
    full_command = command_parts[:1] + base_ssh_args + command_parts[1:]
    print(f"Executing: {' '.join(full_command)}")

    process = subprocess.Popen(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line-buffered
    )

    try:
        for line in process.stdout:
            print(line, end="")  # Already includes newline
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        print("[ERROR] Command timed out.")
    return process.returncode


def run_remote_ssh_command(command_to_execute, timeout=60):
    ssh_command = ["ssh", f"{VM_MACHINE_USER}@{VM_MACHINE_IP}", command_to_execute]
    return _run_ssh_command_base(ssh_command, timeout)


def _run_ssh_command_base_capture(
    command_parts: List[str], timeout: int
) -> CapturedSSHResult:
    base_ssh_args = [
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
    ]

    full_command = command_parts[:1] + base_ssh_args + command_parts[1:]
    # print(f"Preparing to execute (Capture): {' '.join(full_command)}") # Optional: for debugging this func

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,  # Key change for capturing
            text=True,
            check=False,  # We'll check returncode manually
            timeout=timeout,
        )
        return CapturedSSHResult(
            returncode=result.returncode,
            stdout=result.stdout.strip(),  # Strip whitespace
            stderr=result.stderr.strip(),  # Strip whitespace
            args=full_command,
        )
    except subprocess.TimeoutExpired:
        # print(f"[ERROR CAPTURE] Command timed out: {' '.join(full_command)}")
        return CapturedSSHResult(
            returncode=-1,  # Or a specific timeout code like signal.SIGALRM
            stdout="",
            stderr=f"Command timed out after {timeout} seconds.",
            args=full_command,
        )
    except FileNotFoundError:
        # print(f"[ERROR CAPTURE] SSH command not found: {full_command[0]}")
        return CapturedSSHResult(
            returncode=-2,
            stdout="",
            stderr=f"Command not found: {full_command[0]}",
            args=full_command,
        )
    except Exception as e:
        # print(f"[ERROR CAPTURE] Exception during SSH command: {e}")
        return CapturedSSHResult(
            returncode=-3,
            stdout="",
            stderr=f"Exception during command execution: {str(e)}",
            args=full_command,
        )


def run_remote_ssh_command_capture(
    command_to_execute: str, timeout: int = 60
) -> CapturedSSHResult:
    ssh_command_parts = [
        "ssh",
        f"{VM_MACHINE_USER}@{VM_MACHINE_IP}",
        command_to_execute,
    ]
    return _run_ssh_command_base_capture(ssh_command_parts, timeout)


def postprocess_generation_for_deployment(
    generation_dir: str,
    uid: str,
    VM_MACHINE_IP: str,
    VM_MACHINE_USER: str,
    public_deployment: bool = False,
    username: str = "admin",
    password: str = None,
):
    print(f"Postprocessing generation at {generation_dir} for deployment...")
    backend_api_internal_port = 7070
    backend_ws_internal_port = 8765

    # Change the backend config to use only the 7070 port
    config_path = os.path.join(generation_dir, "backend", "config.yaml")
    with open(config_path, "r", encoding="utf8") as f:
        config = yaml.safe_load(f)

    # Modify the port under 'api'
    if "api" in config and isinstance(config["api"], dict):
        config["api"]["port"] = backend_api_internal_port

    # Modify the port under 'websocket'
    if "websocket" in config and isinstance(config["websocket"], dict):
        config["websocket"][
            "host"
        ] = "0.0.0.0"  # Ensure it listens on all interfaces since it has auth
        config["websocket"]["port"] = backend_ws_internal_port

    with open(config_path, "w", encoding="utf8") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Change the frontend env with the correct ip for the backend
    env_path = os.path.join(generation_dir, "frontend", ".env")
    with open(env_path, "r+", encoding="utf8") as f:
        content = f.read()
        updated = re.sub(
            r"^VITE_API_BASE_URL\s*=\s*.*$",
            f"VITE_API_BASE_URL=http://{VM_MACHINE_IP}/apps/{uid}/api/",
            content,
            flags=re.MULTILINE,
        )
        f.seek(0)
        f.write(updated)
        f.truncate()

    traefik_port = 80

    # Change the frontend websocket config with the correct ip for the backend
    ws_path = os.path.join(
        generation_dir, "frontend", "src", "context", "websocketConfig.json"
    )
    with open(ws_path, "r+", encoding="utf8") as f:
        updated_data = {"host": VM_MACHINE_IP, "port": f"{traefik_port}/apps/{uid}/ws/"}
        updated = json.dumps(updated_data, indent=4)
        # Write the new content
        f.seek(0)
        f.write(updated)
        f.truncate()

    # Change the backend app initialization with the correct path
    main_backend_path = os.path.join(generation_dir, "backend", "main.py")
    with open(main_backend_path, "r+", encoding="utf8") as f:
        content = f.read()
        updated = re.sub(
            r"app = FastAPI\(\)",
            f'app = FastAPI(root_path="/apps/{uid}/api")',
            content,
        )
        f.seek(0)
        f.write(updated)
        f.truncate()

    # Inject traefik labels into docker-compose.yml
    compose_path = os.path.join(generation_dir, "docker-compose.yml")
    inject_traefik_labels_and_network(
        compose_path, uid, public=public_deployment, username=username, password=password
    )

