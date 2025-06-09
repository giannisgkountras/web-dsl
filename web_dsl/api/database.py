import aiosqlite
from datetime import datetime
import os
from typing import List, Optional

DATABASE_FILE = "deployments.db"  # Store in current dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.path.join(BASE_DIR, DATABASE_FILE)


async def get_db_connection():
    conn = await aiosqlite.connect(DATABASE_URL)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db():
    # Use 'async with' for connection management
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deployment_uid TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            url TEXT,
            app_username TEXT,
            app_password TEXT,
            is_public INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            docker_project_name TEXT,
            model_dir_local TEXT,
            gen_dir_local TEXT,
            remote_dir_vm TEXT,
            error_message TEXT
        )
        """
        )
        await db.execute(
            """
        CREATE TRIGGER IF NOT EXISTS update_deployments_updated_at
        AFTER UPDATE ON deployments
        FOR EACH ROW
        BEGIN
            UPDATE deployments SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_id ON deployments (user_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_status ON deployments (status)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_is_public ON deployments (is_public)"
        )
        await db.commit()
    print(f"Database initialized at {DATABASE_URL}")


# ======= CRUD Operations ========


async def db_create_deployment_record(
    conn: aiosqlite.Connection,
    deployment_uid: str,
    user_id: str,
    is_public: bool,
    model_dir_local: str,
    gen_dir_local: str,
    remote_dir_vm: str,
    docker_project_name: str,
) -> int:  # Returns lastrowid
    now = datetime.now()
    async with conn.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO deployments (deployment_uid, user_id, is_public, status,
                                     model_dir_local, gen_dir_local, remote_dir_vm,
                                     docker_project_name, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
        """,
            (
                deployment_uid,
                user_id,
                1 if is_public else 0,
                model_dir_local,
                gen_dir_local,
                remote_dir_vm,
                docker_project_name,
                now,
                now,
            ),
        )  # Passing datetime objects
        await conn.commit()
        return cursor.lastrowid


async def db_update_deployment_status(
    conn: aiosqlite.Connection,
    deployment_uid: str,
    status: str,
    url: Optional[str] = None,
    app_username: Optional[str] = None,
    app_password: Optional[str] = None,
    error_message: Optional[str] = None,
):
    query_parts = ["status = ?", "updated_at = ?"]
    params = [status, datetime.now()]  # Passing datetime object

    if url is not None:
        query_parts.append("url = ?")
        params.append(url)
    if app_username is not None:
        query_parts.append("app_username = ?")
        params.append(app_username)
    if app_password is not None:
        query_parts.append("app_password = ?")
        params.append(app_password)
    if error_message is not None:
        query_parts.append("error_message = ?")
        params.append(error_message)

    query = f"UPDATE deployments SET {', '.join(query_parts)} WHERE deployment_uid = ?"
    params.append(deployment_uid)

    await conn.execute(query, tuple(params))
    await conn.commit()


async def db_get_deployment_by_uid(
    conn: aiosqlite.Connection, deployment_uid: str
) -> Optional[aiosqlite.Row]:
    async with conn.execute(
        "SELECT * FROM deployments WHERE deployment_uid = ?", (deployment_uid,)
    ) as cursor:
        return await cursor.fetchone()


async def db_get_deployments_by_user_id(
    conn: aiosqlite.Connection, user_id: str
) -> List[aiosqlite.Row]:
    async with conn.execute(
        "SELECT * FROM deployments WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ) as cursor:
        return await cursor.fetchall()


async def db_get_public_deployments(conn: aiosqlite.Connection) -> List[aiosqlite.Row]:
    async with conn.execute(
        "SELECT * FROM deployments WHERE is_public = 1 AND status = 'running' ORDER BY created_at DESC"
    ) as cursor:
        return await cursor.fetchall()


async def db_get_running_deployments_by_user_id(
    conn: aiosqlite.Connection, user_id: str
) -> List[aiosqlite.Row]:
    async with conn.execute(
        "SELECT * FROM deployments WHERE user_id = ? AND status = 'running'", (user_id,)
    ) as cursor:
        return await cursor.fetchall()


async def db_get_all_deployments(conn: aiosqlite.Connection) -> List[aiosqlite.Row]:
    async with conn.execute(
        "SELECT * FROM deployments ORDER BY created_at DESC"
    ) as cursor:
        return await cursor.fetchall()


async def db_delete_deployment_by_uid(
    conn: aiosqlite.Connection, deployment_uid: str
) -> None:
    await conn.execute(
        "DELETE FROM deployments WHERE deployment_uid = ?", (deployment_uid,)
    )
    await conn.commit()
