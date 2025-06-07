import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .config import TMP_DIR
from .routers import validation, generation, deployment, transformations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Application startup: Initializing database...")
    await init_db()
    os.makedirs(TMP_DIR, exist_ok=True)
    print("Application startup: Database initialized")
    yield
    # Code to run on shutdown (e.g., close a global connection pool if you had one)
    print("Application shutdown: Cleaning up...")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(validation.router)
app.include_router(generation.router)
app.include_router(deployment.router)
app.include_router(transformations.router)
