from fastapi import FastAPI
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from src.database.connection import initialize_database
from .config import settings
from .routes.users import user_router

import logging.config
from src.utils.logging import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    yield

app = FastAPI(
    lifespan=lifespan
)
app.include_router(user_router)

for field_name, value in settings.model_dump().items():
    if value is None or value == "":
        raise EnvironmentError(
            f"환경변수 '{field_name}' 를 찾을 수 없거나 값이 설정되지 않았습니다.")


Instrumentator().instrument(app).expose(app)
