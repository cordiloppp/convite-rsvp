from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import Base, get_db
from app.main import app
from app.models import Event, Guest, Planner
from app.security import create_access_token, hash_password

TEST_PASSWORD = "contrasena-de-prueba"


@pytest.fixture(scope="session")
def test_engine():
    """Crea una base de pruebas limpia y la migra con Alembic."""
    settings = get_settings()
    test_db = f"{settings.postgres_db}_test"

    admin = create_engine(settings.url_for("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{test_db}"'))

    engine = create_engine(settings.url_for(test_db))
    config = Config("alembic.ini")
    with engine.begin() as conn:
        config.attributes["connection"] = conn
        command.upgrade(config, "head")

    yield engine

    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def db(test_engine) -> Iterator[Session]:
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with factory() as session:
        yield session
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with test_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_planner(db: Session):
    def _make(email: str = "ana@example.com", nombre: str = "Ana") -> Planner:
        planner = Planner(nombre=nombre, email=email, password_hash=hash_password(TEST_PASSWORD))
        db.add(planner)
        db.commit()
        return planner

    return _make


@pytest.fixture
def make_event(db: Session):
    def _make(planner: Planner, limite_en_dias: int = 20, nombre: str = "Boda de prueba") -> Event:
        now = datetime.now(UTC)
        event = Event(
            planner_id=planner.id,
            nombre=nombre,
            tipo="boda",
            fecha_hora=now + timedelta(days=30),
            lugar_nombre="Salón Jardín",
            direccion="Blvd. Agua Caliente 100, Tijuana",
            fecha_limite_confirmacion=now + timedelta(days=limite_en_dias),
        )
        db.add(event)
        db.commit()
        return event

    return _make


@pytest.fixture
def make_guest(db: Session):
    def _make(event: Event, nombre: str = "Familia López", lugares: int = 4, **fields) -> Guest:
        guest = Guest(
            event_id=event.id, nombre_grupo=nombre, lugares_asignados=lugares, **fields
        )
        db.add(guest)
        db.commit()
        return guest

    return _make


@pytest.fixture
def auth_headers():
    def _headers(planner: Planner) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(planner.id)}"}

    return _headers
