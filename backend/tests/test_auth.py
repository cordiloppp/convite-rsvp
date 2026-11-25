from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.models import Event, Guest
from app.security import ALGORITHM
from tests.conftest import TEST_PASSWORD


def test_health_y_config(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/config").json()["brand_name"] == get_settings().brand_name


def test_login_correcto_da_acceso_a_me(client, make_planner):
    make_planner("ana@example.com")
    response = client.post(
        "/api/auth/login", json={"email": " Ana@Example.com ", "password": TEST_PASSWORD}
    )
    assert response.status_code == 200

    token = response.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"
    assert "password_hash" not in me.json()


@pytest.mark.parametrize(
    ("email", "password"),
    [("ana@example.com", "incorrecta"), ("nadie@example.com", TEST_PASSWORD)],
)
def test_login_invalido_da_el_mismo_error(client, make_planner, email, password):
    make_planner("ana@example.com")
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_me_exige_token_valido(client, make_planner):
    planner = make_planner()
    assert client.get("/api/auth/me").status_code == 401

    bad_headers = {"Authorization": "Bearer no-es-un-token"}
    assert client.get("/api/auth/me", headers=bad_headers).status_code == 401

    expired = jwt.encode(
        {"sub": str(planner.id), "exp": datetime.now(UTC) - timedelta(minutes=1)},
        get_settings().jwt_secret,
        algorithm=ALGORITHM,
    )
    expired_headers = {"Authorization": f"Bearer {expired}"}
    assert client.get("/api/auth/me", headers=expired_headers).status_code == 401


def test_la_base_rechaza_confirmar_mas_lugares_que_los_asignados(db, make_planner):
    now = datetime.now(UTC)
    event = Event(
        planner_id=make_planner().id,
        nombre="Boda",
        tipo="boda",
        fecha_hora=now + timedelta(days=30),
        lugar_nombre="Salón",
        direccion="Tijuana",
        fecha_limite_confirmacion=now + timedelta(days=20),
    )
    db.add(event)
    db.commit()

    db.add(
        Guest(
            event_id=event.id,
            nombre_grupo="Familia López",
            lugares_asignados=2,
            lugares_confirmados=3,
            estado="confirmado",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
