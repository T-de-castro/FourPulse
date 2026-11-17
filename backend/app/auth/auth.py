from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_senha(senha: str) -> str:
    pwd_bytes = senha.encode("utf-8")
    if len(pwd_bytes) > 72:
        raise ValueError("A senha não pode exceder 72 bytes (limite de segurança bcrypt).")
    if len(senha) < 8:
        raise ValueError("A senha deve possuir no mínimo 8 caracteres.")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verificar_senha(senha: str, hash_str: str) -> bool:
    try:
        pwd_bytes = senha.encode("utf-8")
        if len(pwd_bytes) > 72:
            return False
        hash_bytes = hash_str.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def criar_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
