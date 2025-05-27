import os
from fastapi.security import APIKeyHeader
from fastapi import HTTPException, status, Security
from dotenv import load_dotenv

load_dotenv()

TMP_DIR = "./tmp/"
API_KEY = os.getenv("API_KEY", "API_KEY")
api_keys = [API_KEY]
api_key_header = APIKeyHeader(name="X-API-Key")
CLEANUP_THRESHOLD = 60 * 15  # 15m in seconds
VM_MACHINE_IP = os.getenv("VM_MACHINE_IP", "")
VM_MACHINE_USER = os.getenv("VM_MACHINE_USER", "")
VM_MACHINE_SSH_PORT = os.getenv("VM_MACHINE_SSH_PORT", "22")
# SSH_KEY_PATH = "/root/.ssh/id_ed25519"  # Path to the private key in the container
SSH_KEY_PATH = "/home/ankel/.ssh/id_ed25519"


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
    )
