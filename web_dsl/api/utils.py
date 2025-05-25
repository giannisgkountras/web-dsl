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

from passlib.hash import md5_crypt
from fastapi import UploadFile


def inject_traefik_labels_and_network(
    compose_path: str,
    uid: str,
    backend_internal_port: int = 8080,
    free_port: int = None,
):
    username = "admin"
    password = secrets.token_urlsafe(16)

    # Call htpasswd -nb to generate the hash
    result = subprocess.run(
        ["htpasswd", "-nb", username, password],
        capture_output=True,
        text=True,
        check=True,
    )

    hashed_result = result.stdout.strip()

    escaped_hashed_result = hashed_result.replace("$", "$$")

    with open(compose_path, "r") as f:
        compose_content = f.read()
        compose = yaml.safe_load(compose_content)

    api_full_path_prefix = f"/apps/{uid}/api/"

    compose["networks"] = {"traefik-demo": {"external": True}}

    for svc_name, svc_config in compose.get("services", {}).items():
        # Remove any direct port bindings
        svc_config.pop("ports", None)

        # Expose the free port for the websocket connection
        if svc_name == "backend":
            svc_config["ports"] = (
                [
                    # I will always make 9999 to be used for the websocket connection internally
                    f"{free_port}:9999"
                ]
                if free_port
                else []
            )

        # Attach all services to the 'proxy' network for inter-service communication
        #    and for Traefik to discover the frontend.
        svc_config["networks"] = ["traefik-demo"]

        if svc_name == "frontend":
            labels = [
                "traefik.enable=true",
                # Route /apps/<uid>/* to this service
                f"traefik.http.routers.{uid}-frontend.rule=PathPrefix(`/apps/{uid}/`)",
                f"traefik.http.routers.{uid}-frontend.entrypoints=web",
                f"traefik.http.routers.{uid}-frontend.priority=10",
                f"traefik.http.services.{uid}-frontend.loadbalancer.server.port=80",
                # add auth to the frontend
                f"traefik.http.middlewares.{uid}-frontend-auth.basicauth.users={escaped_hashed_result}",
                f"traefik.http.routers.{uid}-frontend.middlewares={uid}-frontend-auth",
            ]
            svc_config["labels"] = labels

        elif svc_name == "backend":
            labels = [
                "traefik.enable=true",
                f"traefik.http.routers.{uid}-backend.rule=PathPrefix(`{api_full_path_prefix}`)",
                f"traefik.http.routers.{uid}-backend.priority=20",  # Higher priority
                f"traefik.http.routers.{uid}-backend.entrypoints=web",
                f"traefik.http.services.{uid}-backend.loadbalancer.server.port={backend_internal_port}",
                # # Strip the /apps/uid/api prefix for requests going to the backend app
                # f"traefik.http.middlewares.{uid}-backend-stripprefix.stripprefix.prefixes={api_full_path_prefix}",
                # f"traefik.http.routers.{uid}-backend.middlewares={uid}-backend-stripprefix",
            ]
            # Traefik labels for Backend API
            svc_config["labels"] = labels
        else:
            svc_config.pop("labels", None)

    # Write back out
    with open(compose_path, "w") as f:
        yaml.dump(compose, f, sort_keys=False)

    return username, password


def find_free_port_on_vm(VM_MACHINE_IP: str, VM_MACHINE_USER: str) -> int:
    result = subprocess.run(
        [
            "ssh",
            f"{VM_MACHINE_USER}@{VM_MACHINE_IP}",
            "python3 -c \"import socket; s=socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()\"",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Strip and convert output to int
    free_port = int(result.stdout.strip())
    return free_port


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


def postprocess_generation_for_deployment(
    generation_dir: str,
    uid: str,
    VM_MACHINE_IP: str,
    VM_MACHINE_USER: str,
):

    # Change the backend config to use only the 8080 port
    config_path = os.path.join(generation_dir, "backend", "config.yaml")
    with open(config_path, "r", encoding="utf8") as f:
        config = yaml.safe_load(f)

    # Modify the port under 'api'
    if "api" in config and isinstance(config["api"], dict):
        config["api"]["port"] = 8080

    # Modify the port under 'websocket'
    if "websocket" in config and isinstance(config["websocket"], dict):
        config["websocket"][
            "host"
        ] = "0.0.0.0"  # Ensure it listens on all interfaces since it has auth
        config["websocket"]["port"] = 9999

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

    free_port = find_free_port_on_vm(VM_MACHINE_IP, VM_MACHINE_USER)

    # Change the frontend websocket config with the correct ip for the backend
    ws_path = os.path.join(
        generation_dir, "frontend", "src", "context", "websocketConfig.json"
    )
    with open(ws_path, "r+", encoding="utf8") as f:
        updated_data = {"host": VM_MACHINE_IP, "port": free_port}
        updated = json.dumps(updated_data, indent=4)
        # Write the new content
        f.seek(0)
        f.write(updated)
        f.truncate()

    # Find a random open port on the VM machine
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
    username, password = inject_traefik_labels_and_network(
        compose_path, uid, free_port=free_port
    )

    return username, password
