from typing import Annotated
import logging
from fastapi import Depends, HTTPException, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError

from ..config import settings
from ..schemas.jwt import TokenData
from ..repositories.user_repository import UserRepository

logger = logging.getLogger("prod")
user_repo = UserRepository()
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


def build_decode_kwargs() -> dict:
    kwargs = {
        "key": settings.SECRET_KEY,
        "algorithms": [settings.JWT_ALGORITHM],
        "options": {"verify_aud": bool(getattr(settings, "JWT_AUDIENCE", None))},
        "leeway": getattr(settings, "JWT_LEEWAY_SECONDS", 0),
    }
    if getattr(settings, "JWT_AUDIENCE", None):
        kwargs["audience"] = settings.JWT_AUDIENCE
    if getattr(settings, "JWT_ISSUER", None):
        kwargs["issuer"] = settings.JWT_ISSUER
    return kwargs


def extract_user_id(payload: dict) -> int:
    claim_name = getattr(settings, "JWT_USER_ID_CLAIM", "sub")
    raw_user_id = payload.get(claim_name)
    if raw_user_id is None:
        raise credentials_exception
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        raise credentials_exception


async def get_http_token_payload(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    try:
        payload = jwt.decode(token, **build_decode_kwargs())
        user_id = extract_user_id(payload)
        await user_repo.get_or_create_by_user_id(user_id)
        return TokenData(user_id=user_id)
    except ExpiredSignatureError:
        raise expired_token_exception
    except JWTError:
        raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        logger.exception("get_http_token_payload 처리 중 예기치 못한 오류")
        raise credentials_exception


async def get_ws_token_payload(websocket: WebSocket) -> TokenData:
    token = websocket.query_params.get("token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        payload = jwt.decode(token, **build_decode_kwargs())
        user_id = extract_user_id(payload)
        return TokenData(user_id=user_id)
    except ExpiredSignatureError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    except (JWTError, ValueError, TypeError):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
