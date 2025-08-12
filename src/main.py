from fastapi import FastAPI
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from fastapi.middleware.cors import CORSMiddleware

from src.database.connection import initialize_database
from .config import settings
from .routers.dashboard import dashboard_router
from .routers.textneck import textneck_router
import logging.config
from src.utils.logging import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    yield

app = FastAPI(
    lifespan=lifespan,
    docs_url="/core/docs",
    redoc_url="/core/redoc",
    openapi_url="/core/openapi.json"
)

origins = [
    "https://www.textneckhub.p-e.kr"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(dashboard_router, prefix="/core/v1")
app.include_router(textneck_router, prefix="/core/v1")

for field_name, value in settings.model_dump().items():
    if value is None or value == "":
        raise EnvironmentError(
            f"환경변수 '{field_name}' 를 찾을 수 없거나 값이 설정되지 않았습니다.")


Instrumentator().instrument(app).expose(app)
