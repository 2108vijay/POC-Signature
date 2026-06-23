from datetime import datetime, timedelta
from jose import jwt, JWTError
from SRC.core.config import config


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise JWTError("No subject in token")
        return username
    except JWTError as e:
        raise JWTError(str(e))