from datetime import UTC, datetime

from app.models import Event, Guest, GuestStatus
from app.schemas.public import RsvpIn


class RsvpError(Exception):
    """Respuesta rechazada; el mensaje se muestra al invitado."""


class RsvpCerrado(RsvpError):
    pass


class LugaresInvalidos(RsvpError):
    pass


def puede_responder(event: Event) -> bool:
    return datetime.now(UTC) <= event.fecha_limite_confirmacion


def aplicar_respuesta(guest: Guest, data: RsvpIn) -> None:
    if not puede_responder(guest.event):
        raise RsvpCerrado("La fecha límite para confirmar ya pasó")

    if data.asistira:
        lugares = data.lugares
        if lugares is None or not 1 <= lugares <= guest.lugares_asignados:
            raise LugaresInvalidos(
                f"Puedes confirmar de 1 a {guest.lugares_asignados} lugares"
            )
        guest.estado = GuestStatus.CONFIRMADO.value
        guest.lugares_confirmados = lugares
    else:
        guest.estado = GuestStatus.RECHAZADO.value
        guest.lugares_confirmados = 0

    guest.nota = data.nota
    guest.confirmado_at = datetime.now(UTC)
