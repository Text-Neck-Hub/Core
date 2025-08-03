from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
from ..config import settings
from ..models.users import User
logger = logging.getLogger('prod')


async def initialize_database():
    try:
        client = AsyncIOMotorClient(settings.DATABASE_URL)
        await init_beanie(
            database=client.get_default_database(),
            document_models=[User]
        )
        logger.info('데이터베이스 연결 완료')
    except Exception as e:
        logger.critical(f'데이터베이스 연결 실패: {e}')
        raise (f"데이터베이스 연결 실패: {e}")
