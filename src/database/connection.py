from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
from ..config import settings
from ..models import Log, User

logger = logging.getLogger('prod')


async def initialize_database() -> AsyncIOMotorClient:
    try:
        client = AsyncIOMotorClient(
            settings.DATABASE_URL,
            uuidRepresentation="standard",
            serverSelectionTimeoutMS=5000,
        )
        await client.admin.command("ping")

        db = client[settings.DATABASE_NAME] if getattr(
            settings, "DATABASE_NAME", None) else client.get_default_database()
        if db is None:
            raise RuntimeError("DATABASE_NAME이 없고 URL에도 기본 DB명이 없습니다.")

        await init_beanie(
            database=db,
            document_models=[User, Log],
        )
        logger.info("데이터베이스 연결 완료")
        return client
    except Exception as e:
        logger.critical(f"데이터베이스 연결 실패: {e}", exc_info=True)
        raise RuntimeError(f"데이터베이스 연결 실패: {e}") from e
