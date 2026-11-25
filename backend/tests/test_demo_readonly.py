import pytest

from app.config import get_settings
from app.main import READONLY_MESSAGE
from tests.conftest import TEST_PASSWORD

OWNER_PASSWORD = "clave-privada-del-dueno"
RSVP = "/api/public/invitations/{}/rsvp"


@pytest.fixture
def readonly(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "demo_readonly", True)
    monkeypatch.setattr(settings, "owner_password", OWNER_PASSWORD)


def login(client, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def bearer(response) -> dict[str, str]:
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_config_avisa_el_modo_demo(client, readonly):
    assert client.get("/api/config").json()["demo_readonly"] is True


def test_cuenta_demo_puede_ver_pero_no_modificar(client, readonly, make_planner, make_event, make_guest):
    planner = make_planner("demo@example.com")
    event = make_event(planner)
    guest = make_guest(event)
    headers = bearer(login(client, "demo@example.com", TEST_PASSWORD))

    assert client.get(f"/api/events/{event.id}/panel", headers=headers).status_code == 200

    response = client.delete(f"/api/events/{event.id}/guests/{guest.id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == READONLY_MESSAGE
    assert client.get(f"/api/events/{event.id}/panel", headers=headers).json()


def test_invitado_no_puede_confirmar_en_modo_demo(client, readonly, make_planner, make_event, make_guest):
    guest = make_guest(make_event(make_planner()))
    response = client.post(RSVP.format(guest.token), json={"asistira": True, "lugares": 2})
    assert response.status_code == 403
    assert response.json()["detail"] == READONLY_MESSAGE


def test_clave_del_dueno_puede_modificar(client, readonly, make_planner, make_event, make_guest):
    planner = make_planner("demo@example.com")
    event = make_event(planner)
    guest = make_guest(event)
    headers = bearer(login(client, "demo@example.com", OWNER_PASSWORD))

    response = client.delete(f"/api/events/{event.id}/guests/{guest.id}", headers=headers)
    assert response.status_code == 204


def test_clave_del_dueno_no_abre_cuentas_inexistentes(client, readonly):
    response = login(client, "nadie@example.com", OWNER_PASSWORD)
    assert response.status_code == 401


def test_sin_modo_demo_todo_funciona_normal(client, make_planner, make_event, make_guest):
    planner = make_planner("demo@example.com")
    event = make_event(planner)
    guest = make_guest(event)
    headers = bearer(login(client, "demo@example.com", TEST_PASSWORD))
    response = client.delete(f"/api/events/{event.id}/guests/{guest.id}", headers=headers)
    assert response.status_code == 204


def test_demo_sin_cuenta_da_sesion_de_solo_lectura(client, readonly, make_planner, make_event, make_guest, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_email", "demo@example.com")
    event = make_event(make_planner("demo@example.com"))
    guest = make_guest(event)

    response = client.post("/api/auth/demo")
    assert response.status_code == 200
    headers = bearer(response)

    assert client.get(f"/api/events/{event.id}/panel", headers=headers).status_code == 200
    blocked = client.delete(f"/api/events/{event.id}/guests/{guest.id}", headers=headers)
    assert blocked.status_code == 403


def test_demo_sin_cuenta_no_existe_fuera_del_modo_demo(client, make_planner):
    make_planner("demo@convite.mx")
    assert client.post("/api/auth/demo").status_code == 404
