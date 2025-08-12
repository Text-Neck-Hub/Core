from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status

from ..repositories.log_repository import LogRepository
from ..schemas.logs import Log
from ..auth.authentication import get_http_token_payload
from ..schemas.jwt import TokenData
import logging
logger = logging.getLogger('prod')
log_repo = LogRepository()
dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],

)


@dashboard_router.get("/")
async def get_logs(
    current_user_data: Annotated[TokenData, Depends(get_http_token_payload)]
) -> List[Log] | None:

    logs: List[Log] | None = None

    try:
        logs = await log_repo.get_logs(user_id=current_user_data.user_id, limit=100, offset=0)
    except Exception as e:
        logger.exception(f"유저 설정 ({current_user_data.user_id}) 불러오기 실패: {e}😡🤖")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정을 불러오는 중 서버 오류가 발생했습니다."
        )

    if logs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 설정 정보를 찾을 수 없습니다."
        )

    logging.info(logs)

    return logs.model_dump_json()
