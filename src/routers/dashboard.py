from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status

from ..models.users import User
from ..schemas.logs import Log
from ..database.orm import Database
from ..auth.authentication import get_valid_token_payload
from ..schemas.jwt import TokenData
import logging
logger = logging.getLogger('prod')

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],

)

user_db = Database(User)


@dashboard_router.get("/")
async def get_my_settings(
    current_user_data: Annotated[TokenData, Depends(get_valid_token_payload)]
) -> List[Log] | None:

    user: User | None = None

    try:
        user = await user_db.get_by_user_id(user_id=current_user_data.user_id)
    except Exception as e:
        logger.exception(f"유저 설정 ({current_user_data.user_id}) 불러오기 실패: {e}😡🤖")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정을 불러오는 중 서버 오류가 발생했습니다."
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 설정 정보를 찾을 수 없습니다."
        )

    logging.info(user)

    return user.model_dump_json()
