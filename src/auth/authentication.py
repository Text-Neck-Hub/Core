from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError

from ..config import settings
from ..schemas.jwt import TokenData
from ..models.users import User
import logging
logger = logging.getLogger('prod')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증 실패: 유효하지 않은 토큰입니다.",
    headers={"WWW-Authenticate": "Bearer"},
)
expired_token_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증 실패: 토큰이 만료되었습니다.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_valid_token_payload(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    logger.info('get_valid_token_payload 함수 진입! 토큰 유효성 검사 시작.')

    try:
        logger.debug(f"토큰 디코딩 시도. 토큰 첫 20글자: {token[:20]}...")
        payload = jwt.decode(token,
                             settings.SECRET_KEY,
                             algorithms=[settings.JWT_ALGORITHM],
                             audience=settings.JWT_AUDIENCE,
                             issuer=settings.JWT_ISSUER
                             )
        logger.info(f"토큰 디코딩 성공! 페이로드: {payload}")

        user_id_from_token: int = payload.get(settings.JWT_USER_ID_CLAIM)

        if user_id_from_token is None or not isinstance(user_id_from_token, int):
            logger.error(
                f"페이로드에 유효한 user_id 없음! user_id: {user_id_from_token} (타입: {type(user_id_from_token)})")
            raise credentials_exception

        logger.debug(f"DB에서 사용자 ({user_id_from_token}) 조회 시도.")
        user_in_db = await User.find_one(User.user_id == user_id_from_token)

        logger.info(f"DB 조회 결과: user_in_db={user_in_db is not None}")

        if not user_in_db:
            logger.warning(
                f"사용자 ({user_id_from_token})를 DB에서 찾을 수 없음. 새 사용자 생성 시도.")
            new_user = User(user_id=user_id_from_token)
            try:
                await new_user.create()
                user_in_db = new_user
                logger.info(f"새 사용자 ({user_id_from_token}) 생성 성공!")
            except Exception as e:
                logger.exception(
                    f"새 사용자 ({user_id_from_token}) 생성 중 심각한 오류 발생! 😡🤖")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="사용자 데이터 생성 중 오류 발생"
                )

        logger.info(f"토큰 유효성 검사 및 사용자 확인 완료. user_id: {user_id_from_token}")
        return TokenData(user_id=user_id_from_token)

    except ExpiredSignatureError as e:
        logger.warning(f"만료된 토큰! ExpiredSignatureError: {e}")
        raise expired_token_exception
    except JWTError as e:
        logger.error(f"유효하지 않은 JWT 토큰! JWTError: {e}")
        raise credentials_exception
    except Exception as e:
        logger.exception(f"get_valid_token_payload 함수에서 예상치 못한 오류 발생! 😱")
        raise credentials_exception
