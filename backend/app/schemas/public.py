from pydantic import BaseModel, field_validator

from app.models import EventType, GuestStatus
from app.schemas.common import LocalDateTime, clean_optional


class RsvpIn(BaseModel):
    asistira: bool
    lugares: int | None = None
    nota: str | None = None

    @field_validator("nota")
    @classmethod
    def _nota(cls, value: str | None) -> str | None:
        value = clean_optional(value)
        if value and len(value) > 500:
            raise ValueError("La nota admite máximo 500 caracteres")
        return value


class InvitationEvent(BaseModel):
    nombre: str
    tipo: EventType
    fecha_hora: LocalDateTime
    lugar_nombre: str
    direccion: str
    link_mapa: str
    mensaje: str | None
    imagen_portada_url: str | None
    fecha_limite_confirmacion: LocalDateTime


class InvitationGuest(BaseModel):
    nombre_grupo: str
    lugares_asignados: int
    estado: GuestStatus
    lugares_confirmados: int
    nota: str | None


class Brand(BaseModel):
    nombre: str
    url: str


class InvitationOut(BaseModel):
    """Lo único que ve un invitado: sin teléfono, ids ni datos del planner."""

    event: InvitationEvent
    guest: InvitationGuest
    puede_responder: bool
    timezone: str
    marca: Brand
