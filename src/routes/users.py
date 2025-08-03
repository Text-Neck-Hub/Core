from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from ..models.users import User
from ..database.orm import Database
from ..auth.authentication import get_valid_token_payload
from ..schemas.jwt import TokenData
import logging
logger = logging.getLogger('prod')

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],

)

user_db = Database(User)


@user_router.get("/")
async def get_my_settings(
    current_user_data: Annotated[TokenData, Depends(get_valid_token_payload)]
):
    logger.info('sssssssss')
    my_settings_doc: User | None = None

    try:
        my_settings_doc = await user_db.get(id=current_user_data.user_id)
    except Exception as e:
        logger.exception(f"유저 설정 ({current_user_data.user_id}) 불러오기 실패: {e}😡🤖")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 설정을 불러오는 중 서버 오류가 발생했습니다."
        )

    if my_settings_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 설정 정보를 찾을 수 없습니다."
        )

    logging.info(my_settings_doc)

    return {
        "message": f"{current_user_data.user_id}님의 설정 정보를 성공적으로 가져왔습니다.",
        "settings": 'my_settings',
    }
