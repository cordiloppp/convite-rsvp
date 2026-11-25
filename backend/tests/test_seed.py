from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

import scripts.seed as seed_module
from app.config import get_settings
from app.models import Event, Guest, Planner


def test_seed_crea_demo_y_es_idempotente(db, test_engine, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", sessionmaker(bind=test_engine))
    monkeypatch.setattr(get_settings(), "seed_demo", True)

    seed_module.seed()
    seed_module.seed()

    assert db.scalar(select(func.count()).select_from(Planner)) == 1
    events = list(db.scalars(select(Event).order_by(Event.tipo)))
    assert [event.tipo for event in events] == ["boda", "xv"]

    for event in events:
        guests = list(db.scalars(select(Guest).where(Guest.event_id == event.id)))
        estados = {guest.estado for guest in guests}
        assert len(guests) == 25
        assert estados == {"confirmado", "rechazado", "pendiente"}
        assert any(g.lugares_confirmados < g.lugares_asignados for g in guests if g.estado == "confirmado")
        assert all(guest.telefono.startswith("664555") for guest in guests)


def test_seed_desactivado_no_hace_nada(db, test_engine, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", sessionmaker(bind=test_engine))
    monkeypatch.setattr(get_settings(), "seed_demo", False)

    seed_module.seed()

    assert db.scalar(select(func.count()).select_from(Planner)) == 0
