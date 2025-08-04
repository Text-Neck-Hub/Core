from jose.exceptions import JWTError, ExpiredSignatureError
from ..config import settings
from typing import Dict, Any
from jose import jwt


def verify_token(token: str) -> Dict[str, Any]:

    try:
        decoded_payload = jwt.decode(
            token=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        return decoded_payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
