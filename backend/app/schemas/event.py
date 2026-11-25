from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models import EventType
from app.schemas.common import LocalDateTime, clean_optional

MAX_URL = 500


def _required(value: str, label: str, max_length: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{label} es obligatorio")
    if len(value) > max_length:
        raise ValueError(f"{label} admite máximo {max_length} caracteres")
    return value


def _web_url(value: str | None, label: str, allow_relative: bool = False) -> str | None:
    # Estas URL terminan en un href o src público: solo se aceptan http(s).
    value = clean_optional(value)
    if value is None:
        return None
    if len(value) > MAX_URL:
        raise ValueError(f"{label} admite máximo {MAX_URL} caracteres")
    if allow_relative and value.startswith("/") and not value.startswith("//"):
        return value
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"{label} debe empezar con http:// o https://")
    return value


class EventIn(BaseModel):
    nombre: str
    tipo: EventType
    fecha_hora: LocalDateTime
    lugar_nombre: str
    direccion: str
    link_mapa: str | None = None
    mensaje: str | None = None
    imagen_portada_url: str | None = None
    fecha_limite_confirmacion: LocalDateTime

    @field_validator("nombre")
    @classmethod
    def _nombre(cls, value: str) -> str:
        return _required(value, "El nombre del evento", 200)

    @field_validator("lugar_nombre")
    @classmethod
    def _lugar(cls, value: str) -> str:
        return _required(value, "El nombre del lugar", 200)

    @field_validator("direccion")
    @classmethod
    def _direccion(cls, value: str) -> str:
        return _required(value, "La dirección", 300)

    @field_validator("link_mapa")
    @classmethod
    def _mapa(cls, value: str | None) -> str | None:
        return _web_url(value, "El link del mapa")

    @field_validator("imagen_portada_url")
    @classmethod
    def _portada(cls, value: str | None) -> str | None:
        return _web_url(value, "La imagen de portada", allow_relative=True)

    @field_validator("mensaje")
    @classmethod
    def _mensaje(cls, value: str | None) -> str | None:
        value = clean_optional(value)
        if value and len(value) > 2000:
            raise ValueError("El mensaje admite máximo 2000 caracteres")
        return value

    @model_validator(mode="after")
    def _limite(self) -> "EventIn":
        if self.fecha_limite_confirmacion > self.fecha_hora:
            raise ValueError("La fecha límite no puede ser posterior al evento")
        return self


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo: EventType
    fecha_hora: LocalDateTime
    lugar_nombre: str
    direccion: str
    link_mapa: str | None
    mensaje: str | None
    imagen_portada_url: str | None
    fecha_limite_confirmacion: LocalDateTime
    created_at: LocalDateTime


class Resumen(BaseModel):
    """Lugares: confirmados + no_asistiran + pendientes siempre suman el total."""

    lugares_total: int = 0
    lugares_confirmados: int = 0
    lugares_no_asistiran: int = 0
    lugares_pendientes: int = 0
    familias_total: int = 0
    familias_confirmadas: int = 0
    familias_rechazadas: int = 0
    familias_pendientes: int = 0


class EventListItem(EventOut):
    resumen: Resumen
