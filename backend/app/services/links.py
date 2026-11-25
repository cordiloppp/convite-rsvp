import re
from urllib.parse import quote, quote_plus

from app.config import get_settings
from app.models import Event, Guest


def guest_link(token: str) -> str:
    return f"{get_settings().public_app_url.rstrip('/')}/i/{token}"


def whatsapp_number(telefono: str | None) -> str | None:
    """Número para wa.me. Los de 10 dígitos se asumen de México (+52)."""
    digits = re.sub(r"\D", "", telefono or "")
    if len(digits) == 10:
        return f"52{digits}"
    return digits if 10 < len(digits) <= 15 else None


def whatsapp_url(guest: Guest, event: Event) -> str | None:
    number = whatsapp_number(guest.telefono)
    if number is None:
        return None
    message = (
        f"Hola {guest.nombre_grupo}, nos encantaría contar con ustedes en {event.nombre}. "
        f"Aquí está su invitación para confirmar asistencia: {guest_link(guest.token)}"
    )
    return f"https://wa.me/{number}?text={quote(message, safe='')}"


def map_link(event: Event) -> str:
    if event.link_mapa:
        return event.link_mapa
    query = quote_plus(f"{event.lugar_nombre}, {event.direccion}")
    return f"https://www.google.com/maps/search/?api=1&query={query}"
