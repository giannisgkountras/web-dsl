from pydantic import BaseModel
from typing import List, Optional, NamedTuple
from datetime import datetime


class ValidationModel(BaseModel):
    name: str
    model: str


class TransformationModel(BaseModel):
    name: str
    model: str

class DeploymentStringModel(BaseModel):
    model_str: str
    is_public: bool = False
    user_id: str

class DeploymentInfoBase(BaseModel):
    deployment_uid: str
    user_id: str
    status: str
    url: Optional[str] = None
    app_username: Optional[str] = None
    # app_password is not exposed here for security
    is_public: bool
    created_at: datetime
    updated_at: datetime
    docker_project_name: Optional[str] = None
    error_message: Optional[str] = None


class DeploymentDetailResponse(DeploymentInfoBase):
    id: int  # DB primary key


def format_deployment_response(db_row):
    if db_row is None:
        return None
    return DeploymentDetailResponse(
        id=db_row["id"],
        deployment_uid=db_row["deployment_uid"],
        user_id=db_row["user_id"],
        status=db_row["status"],
        url=db_row["url"],
        app_username=db_row["app_username"],
        is_public=bool(db_row["is_public"]),
        created_at=db_row["created_at"],
        updated_at=db_row["updated_at"],
        docker_project_name=db_row["docker_project_name"],
        error_message=db_row["error_message"],
    )


class UserIDBody(BaseModel):
    user_id: str


class DeploymentActionBody(UserIDBody):
    deployment_uid: str


class DockerStatsResponse(BaseModel):
    container_id: str
    cpu_percent: str
    memory_usage: str
    memory_limit: str  # Added from standard docker stats format
    memory_percent: str  # Added
    net_io: str
    block_io: str
    pids: str  # Added
    raw_output: str


class CapturedSSHResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str
    args: List[str]  # The command that was run
