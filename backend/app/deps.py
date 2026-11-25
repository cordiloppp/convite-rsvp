from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Event, Planner
from app.security import decode_access_token

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)


def get_current_planner(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Planner:
    planner_id = decode_access_token(credentials.credentials) if credentials else None
    planner = db.get(Planner, planner_id) if planner_id is not None else None
    if planner is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no válida o expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return planner


CurrentPlanner = Annotated[Planner, Depends(get_current_planner)]


def get_owned_event(event_id: int, db: DbSession, planner: CurrentPlanner) -> Event:
    # 404 también para eventos ajenos: no se revela que existen.
    event = db.scalar(select(Event).where(Event.id == event_id, Event.planner_id == planner.id))
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return event


OwnedEvent = Annotated[Event, Depends(get_owned_event)]
