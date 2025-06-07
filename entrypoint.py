import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import sys

# Load environment variables from .env
dotenv_path = "/app/.env"
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Environment variables
remote_host = os.getenv("VM_MACHINE_IP")
remote_user = os.getenv("VM_MACHINE_USER")
remote_password = os.getenv("VM_MACHINE_PASSWORD")
remote_ssh_port = os.getenv("VM_MACHINE_SSH_PORT", "22")

# SSH key paths
ssh_dir = Path("/root/.ssh")
ssh_key = ssh_dir / "id_ed25519"
ssh_pub_key = ssh_dir / "id_ed25519.pub"

# Create .ssh directory if needed
ssh_dir.mkdir(parents=True, exist_ok=True)

# Generate SSH key if not present
if not ssh_key.exists():
    print("SSH key not found. Generating new SSH key...")
    try:
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(ssh_key)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("SSH key generated successfully.")
    except Exception as e:
        print(f"[ERROR] Unexpected error during SSH key generation: {e}. Exiting.")
        sys.exit(1)

if remote_host and remote_user and remote_password:
    print(f"Attempting to copy SSH key to {remote_user}@{remote_host}...")
    ssh_command = [
        "timeout",
        "20",
        "sshpass",
        "-p",
        remote_password,
        "ssh-copy-id",
        "-p",
        str(remote_ssh_port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "ConnectTimeout=10",
        "-i",
        str(ssh_pub_key),
        f"{remote_user}@{remote_host}",
    ]
    try:
        result = subprocess.run(ssh_command, check=True, capture_output=True, text=True)
        print(f"SSH key copied successfully to {remote_user}@{remote_host}.")
    except Exception as e:
        print(f"[WARNING] Unexpected error during SSH key copy: {e}.")
        print("  Continuing to start the app...")
else:
    print(
        "VM_MACHINE_IP, VM_MACHINE_USER, or VM_MACHINE_PASSWORD not set or incomplete."
    )
    print("Skipping ssh-copy-id. Uvicorn will start.")

print("Starting Uvicorn...")
host = "0.0.0.0"
port = os.getenv("PORT", "8080")
root_path = os.getenv("ROOT_PATH", "")
workers = os.getenv("WORKERS", "1")

uvicorn_command = [
    "uvicorn",
    "web_dsl.api:app",
    "--host",
    host,
    "--port",
    port,
    "--root-path",
    root_path,
    "--workers",
    workers,
]

try:
    os.execvp(uvicorn_command[0], uvicorn_command)
except Exception as e:
    print(f"[ERROR] Failed to start Uvicorn: {e}")
    print("Application will not start.")
    sys.exit(1)
