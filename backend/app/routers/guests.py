from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import DbSession, OwnedEvent
from app.models import Event, Guest
from app.routers.events import guest_out
from app.schemas.guest import GuestIn, GuestOut, ImportResult
from app.services.csv_import import CsvInvalido, parse_guests_csv

router = APIRouter(prefix="/api/events/{event_id}/guests", tags=["guests"])

MAX_CSV_BYTES = 2 * 1024 * 1024


def _locked_guest(db: Session, event: Event, guest_id: int) -> Guest:
    # El bloqueo evita que una edición se cruce con un RSVP en curso.
    guest = db.scalar(
        select(Guest).where(Guest.id == guest_id, Guest.event_id == event.id).with_for_update()
    )
    if guest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invitado no encontrado")
    return guest


@router.post("", response_model=GuestOut, status_code=status.HTTP_201_CREATED)
def create_guest(data: GuestIn, event: OwnedEvent, db: DbSession) -> GuestOut:
    guest = Guest(event_id=event.id, **data.model_dump())
    db.add(guest)
    db.commit()
    return guest_out(guest, event)


@router.post("/import", response_model=ImportResult)
def import_guests(file: UploadFile, event: OwnedEvent, db: DbSession) -> ImportResult:
    content = file.file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="El archivo supera 2 MB")

    existing = db.scalars(select(Guest.nombre_grupo).where(Guest.event_id == event.id))
    try:
        guests, errors = parse_guests_csv(content, existing)
    except CsvInvalido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.add_all(Guest(event_id=event.id, **guest.model_dump()) for guest in guests)
    db.commit()
    return ImportResult(importados=len(guests), errores=errors)


@router.put("/{guest_id}", response_model=GuestOut)
def update_guest(guest_id: int, data: GuestIn, event: OwnedEvent, db: DbSession) -> GuestOut:
    guest = _locked_guest(db, event, guest_id)
    if data.lugares_asignados < guest.lugares_confirmados:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=(
                f"Esta familia ya confirmó {guest.lugares_confirmados} lugares: "
                "no puedes asignarle menos."
            ),
        )
    for field, value in data.model_dump().items():
        setattr(guest, field, value)
    db.commit()
    return guest_out(guest, event)


@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(guest_id: int, event: OwnedEvent, db: DbSession) -> None:
    db.delete(_locked_guest(db, event, guest_id))
    db.commit()
