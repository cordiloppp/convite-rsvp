import re

from pydantic import BaseModel, field_validator

from app.models import GuestStatus
from app.schemas.common import LocalDateTime, clean_optional
from app.schemas.event import EventOut, Resumen

MAX_LUGARES = 100


class GuestIn(BaseModel):
    nombre_grupo: str
    telefono: str | None = None
    lugares_asignados: int | str

    @field_validator("nombre_grupo")
    @classmethod
    def _nombre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre del grupo es obligatorio")
        if len(value) > 200:
            raise ValueError("El nombre del grupo admite máximo 200 caracteres")
        return value

    @field_validator("telefono")
    @classmethod
    def _telefono(cls, value: str | None) -> str | None:
        value = clean_optional(value)
        if value is None:
            return None
        if len(value) > 30 or not re.fullmatch(r"[\d\s()+.-]+", value):
            raise ValueError("El teléfono no es válido")
        if not 10 <= len(re.sub(r"\D", "", value)) <= 15:
            raise ValueError("El teléfono debe tener al menos 10 dígitos")
        return value

    @field_validator("lugares_asignados")
    @classmethod
    def _lugares(cls, value: int | str) -> int:
        try:
            lugares = int(str(value).strip())
        except ValueError:
            raise ValueError("Los lugares asignados deben ser un número entero") from None
        if not 1 <= lugares <= MAX_LUGARES:
            raise ValueError(f"Los lugares asignados deben estar entre 1 y {MAX_LUGARES}")
        return lugares


class GuestOut(BaseModel):
    id: int
    nombre_grupo: str
    telefono: str | None
    lugares_asignados: int
    token: str
    estado: GuestStatus
    lugares_confirmados: int
    nota: str | None
    confirmado_at: LocalDateTime | None
    link: str
    whatsapp_url: str | None


class EventPanel(BaseModel):
    """Todo lo que necesita el panel en una sola consulta, para el polling."""

    event: EventOut
    resumen: Resumen
    guests: list[GuestOut]


class ImportRowError(BaseModel):
    fila: int
    mensaje: str


class ImportResult(BaseModel):
    importados: int
    errores: list[ImportRowError]
