from jose.exceptions import ExpiredSignatureError, JWTError
from jose import jwt
from fastapi import WebSocket, HTTPException, status
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from ..config import settings
from ..schemas.jwt import TokenData
from ..models.users import User
from ..database.orm import Database
import logging

logger = logging.getLogger('prod')
user_repo = Database(User)

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

        decode_kwargs = {
            "key": settings.SECRET_KEY,
            "algorithms": [settings.JWT_ALGORITHM],
        }
        if getattr(settings, "JWT_AUDIENCE", None):
            decode_kwargs["audience"] = settings.JWT_AUDIENCE
        if getattr(settings, "JWT_ISSUER", None):
            decode_kwargs["issuer"] = settings.JWT_ISSUER

        payload = jwt.decode(token, **decode_kwargs)

        safe_claims = {k: payload.get(k) for k in (
            "sub", "jti", "iss", "aud", "exp")}
        logger.info(f"토큰 디코딩 성공! 핵심 클레임: {safe_claims}")

        claim_name = getattr(settings, "JWT_USER_ID_CLAIM", "sub")
        raw_user_id = payload.get(claim_name)
        if raw_user_id is None:
            logger.error("페이로드에 user_id 클레임이 없습니다.")
            raise credentials_exception

        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            logger.error(
                f"user_id 클레임 타입/값이 올바르지 않습니다. raw={raw_user_id} type={type(raw_user_id)}")
            raise credentials_exception

        logger.debug(f"DB에서 사용자 ({user_id}) 조회 시도.")
        user_in_db = await user_repo.find_one({"user_id": user_id})
        logger.info(f"DB 조회 결과: user_in_db={user_in_db is not None}")

        if not user_in_db:
            logger.warning(f"사용자 ({user_id})를 DB에서 찾을 수 없음. 새 사용자 생성 시도.")
            try:
                user_in_db = await user_repo.save(User(user_id=user_id))
                logger.info(f"새 사용자 ({user_id}) 생성 성공!")
            except Exception:
                logger.exception("새 사용자 생성 중 오류 발생.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="사용자 데이터 생성 중 오류 발생"
                )

        logger.info(f"토큰 유효성 검사 및 사용자 확인 완료. user_id: {user_id}")
        return TokenData(user_id=user_id)

    except ExpiredSignatureError as e:
        logger.warning(f"만료된 토큰! ExpiredSignatureError: {e}")
        raise expired_token_exception
    except JWTError as e:
        logger.error(f"유효하지 않은 JWT 토큰! JWTError: {e}")
        raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        logger.exception("get_valid_token_payload 함수에서 예상치 못한 오류 발생!")
        raise credentials_exception


async def get_ws_token_payload(websocket: WebSocket) -> TokenData:
    token = websocket.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 실패: 토큰이 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decode_kwargs = {
        "key": settings.SECRET_KEY,
        "algorithms": [settings.JWT_ALGORITHM],
    }
    if getattr(settings, "JWT_AUDIENCE", None):
        decode_kwargs["audience"] = settings.JWT_AUDIENCE
    if getattr(settings, "JWT_ISSUER", None):
        decode_kwargs["issuer"] = settings.JWT_ISSUER

    try:
        payload = jwt.decode(token, **decode_kwargs)
        claim_name = getattr(settings, "JWT_USER_ID_CLAIM", "sub")
        raw_user_id = payload.get(claim_name)
        user_id = int(raw_user_id)
        return TokenData(user_id=user_id)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 실패: 토큰이 만료되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 실패: 유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
