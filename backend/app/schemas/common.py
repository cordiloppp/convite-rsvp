from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any

from pydantic import AfterValidator, PlainSerializer

from app.config import get_settings


def _attach_timezone(value: datetime) -> datetime:
    """Una fecha sin zona horaria se interpreta en la zona de la app."""
    return value.replace(tzinfo=get_settings().timezone) if value.tzinfo is None else value


def _to_local_iso(value: datetime) -> str:
    return value.astimezone(get_settings().timezone).isoformat()


LocalDateTime = Annotated[
    datetime,
    AfterValidator(_attach_timezone),
    PlainSerializer(_to_local_iso, return_type=str, when_used="json"),
]


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


def first_validation_message(errors: Sequence[Any]) -> str:
    """Convierte los errores de Pydantic en una frase para mostrar al usuario."""
    if not errors:
        return "Datos no válidos"
    error = errors[0]
    if error["type"] == "value_error":
        return error["msg"].removeprefix("Value error, ")
    field = next((part for part in reversed(error["loc"]) if isinstance(part, str)), None)
    return f"Revisa el campo «{field}»" if field else "Datos no válidos"
