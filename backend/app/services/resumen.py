from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Guest, GuestStatus
from app.schemas.event import Resumen


def resumen_por_evento(db: Session, event_ids: Iterable[int]) -> dict[int, Resumen]:
    """Calcula el resumen de varios eventos. Un evento sin invitados da todo en cero."""
    ids = list(event_ids)
    resumenes = {event_id: Resumen() for event_id in ids}
    if not ids:
        return resumenes

    es_pendiente = Guest.estado == GuestStatus.PENDIENTE.value
    rows = db.execute(
        select(
            Guest.event_id,
            func.sum(Guest.lugares_asignados),
            func.sum(Guest.lugares_confirmados),
            func.coalesce(func.sum(Guest.lugares_asignados).filter(es_pendiente), 0),
            func.count(),
            func.count().filter(Guest.estado == GuestStatus.CONFIRMADO.value),
            func.count().filter(Guest.estado == GuestStatus.RECHAZADO.value),
            func.count().filter(es_pendiente),
        )
        .where(Guest.event_id.in_(ids))
        .group_by(Guest.event_id)
    )
    for event_id, total, confirmados, pendientes, familias, conf, rech, pend in rows:
        resumenes[event_id] = Resumen(
            lugares_total=total,
            lugares_confirmados=confirmados,
            # Incluye familias que rechazaron y sobrantes de confirmaciones parciales.
            lugares_no_asistiran=total - confirmados - pendientes,
            lugares_pendientes=pendientes,
            familias_total=familias,
            familias_confirmadas=conf,
            familias_rechazadas=rech,
            familias_pendientes=pend,
        )
    return resumenes
