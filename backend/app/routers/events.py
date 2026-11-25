import re
from urllib.parse import quote

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from app.deps import CurrentPlanner, DbSession, OwnedEvent
from app.models import Event, Guest
from app.schemas.event import EventIn, EventListItem, EventOut
from app.schemas.guest import EventPanel, GuestOut
from app.services.links import guest_link, whatsapp_url
from app.services.resumen import resumen_por_evento
from app.services.xlsx_export import build_workbook

router = APIRouter(prefix="/api/events", tags=["events"])

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def guest_out(guest: Guest, event: Event) -> GuestOut:
    return GuestOut(
        id=guest.id,
        nombre_grupo=guest.nombre_grupo,
        telefono=guest.telefono,
        lugares_asignados=guest.lugares_asignados,
        token=guest.token,
        estado=guest.estado,
        lugares_confirmados=guest.lugares_confirmados,
        nota=guest.nota,
        confirmado_at=guest.confirmado_at,
        link=guest_link(guest.token),
        whatsapp_url=whatsapp_url(guest, event),
    )


def _guests_of(db: DbSession, event: Event) -> list[Guest]:
    return list(
        db.scalars(
            select(Guest).where(Guest.event_id == event.id).order_by(Guest.nombre_grupo, Guest.id)
        )
    )


@router.get("", response_model=list[EventListItem])
def list_events(db: DbSession, planner: CurrentPlanner) -> list[EventListItem]:
    events = list(
        db.scalars(
            select(Event).where(Event.planner_id == planner.id).order_by(Event.fecha_hora)
        )
    )
    resumenes = resumen_por_evento(db, [event.id for event in events])
    return [
        EventListItem(
            **EventOut.model_validate(event).model_dump(), resumen=resumenes[event.id]
        )
        for event in events
    ]


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(data: EventIn, db: DbSession, planner: CurrentPlanner) -> Event:
    event = Event(planner_id=planner.id, **data.model_dump())
    db.add(event)
    db.commit()
    return event


@router.get("/{event_id}", response_model=EventOut)
def get_event(event: OwnedEvent) -> Event:
    return event


@router.put("/{event_id}", response_model=EventOut)
def update_event(data: EventIn, event: OwnedEvent, db: DbSession) -> Event:
    for field, value in data.model_dump().items():
        setattr(event, field, value)
    db.commit()
    return event


@router.get("/{event_id}/panel", response_model=EventPanel)
def event_panel(event: OwnedEvent, db: DbSession) -> EventPanel:
    return EventPanel(
        event=EventOut.model_validate(event),
        resumen=resumen_por_evento(db, [event.id])[event.id],
        guests=[guest_out(guest, event) for guest in _guests_of(db, event)],
    )


@router.get("/{event_id}/export")
def export_guests(event: OwnedEvent, db: DbSession) -> Response:
    content = build_workbook(
        event, _guests_of(db, event), resumen_por_evento(db, [event.id])[event.id]
    )
    slug = re.sub(r"[^a-z0-9]+", "-", event.nombre.lower()).strip("-") or "evento"
    filename = f"invitados-{slug}.xlsx"
    return Response(
        content,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
