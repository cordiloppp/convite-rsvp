import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings

ALGORITHM = "HS256"

# Hash de relleno: el login tarda lo mismo aunque el email no exista,
# así la respuesta no revela qué correos están registrados.
_DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(32), bcrypt.gensalt())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str | None) -> bool:
    candidate = password.encode("utf-8")
    if password_hash is None:
        bcrypt.checkpw(candidate, _DUMMY_HASH)
        return False
    return bcrypt.checkpw(candidate, password_hash.encode("ascii"))


def create_access_token(planner_id: int, can_write: bool = True) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(planner_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "rw": can_write,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Devuelve el id del planner, o None si el token no es válido o expiró."""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None


def token_can_write(token: str) -> bool:
    """True solo si el token es válido y se emitió con permiso de escritura."""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return False
    return payload.get("rw") is True


def owner_password_matches(password: str) -> bool:
    owner = get_settings().owner_password
    return bool(owner) and secrets.compare_digest(password.encode("utf-8"), owner.encode("utf-8"))


def generate_guest_token() -> str:
    return secrets.token_urlsafe(32)
