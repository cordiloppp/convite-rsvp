from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import DbSession
from app.models import Guest
from app.schemas.public import Brand, InvitationEvent, InvitationGuest, InvitationOut, RsvpIn
from app.services.links import map_link
from app.services.rsvp import LugaresInvalidos, RsvpCerrado, aplicar_respuesta, puede_responder

router = APIRouter(prefix="/api/public/invitations", tags=["public"])


def _find_guest(db: Session, token: str, lock: bool = False) -> Guest:
    query = select(Guest).where(Guest.token == token)
    guest = db.scalar(query.with_for_update() if lock else query)
    if guest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invitación no disponible")
    return guest


def _invitation(guest: Guest) -> InvitationOut:
    event = guest.event
    settings = get_settings()
    return InvitationOut(
        event=InvitationEvent(
            nombre=event.nombre,
            tipo=event.tipo,
            fecha_hora=event.fecha_hora,
            lugar_nombre=event.lugar_nombre,
            direccion=event.direccion,
            link_mapa=map_link(event),
            mensaje=event.mensaje,
            imagen_portada_url=event.imagen_portada_url,
            fecha_limite_confirmacion=event.fecha_limite_confirmacion,
        ),
        guest=InvitationGuest(
            nombre_grupo=guest.nombre_grupo,
            lugares_asignados=guest.lugares_asignados,
            estado=guest.estado,
            lugares_confirmados=guest.lugares_confirmados,
            nota=guest.nota,
        ),
        puede_responder=puede_responder(event),
        timezone=settings.app_timezone,
        marca=Brand(nombre=settings.brand_name, url=settings.brand_url),
    )


@router.get("/{token}", response_model=InvitationOut)
def get_invitation(token: str, db: DbSession) -> InvitationOut:
    return _invitation(_find_guest(db, token))


@router.post("/{token}/rsvp", response_model=InvitationOut)
def submit_rsvp(token: str, data: RsvpIn, db: DbSession) -> InvitationOut:
    guest = _find_guest(db, token, lock=True)
    try:
        aplicar_respuesta(guest, data)
    except RsvpCerrado as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except LugaresInvalidos as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return _invitation(guest)
