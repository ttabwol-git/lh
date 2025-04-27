__version__ = "1.0.0"

import os

import uvicorn
from fastapi import FastAPI
from loguru import logger

os.environ["ROOT_PATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__)))
os.environ["SRC_PATH"] = os.path.join(os.getenv("ROOT_PATH"), "src")
os.environ["DATA_PATH"] = os.path.join(os.getenv("ROOT_PATH"), "data")

from src.routers import router

logger.info("Starting FastAPI application...")
app = FastAPI(
    title="Experienced Backend Engineer - Technical Interview",
    description="This spec holds the specification for the API that should be ideated as part of the technical"
    " interview.",
    version=__version__,
)
app.include_router(router)
logger.success(f"FastAPI application started successfully - version {__version__}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
