import pytest


@pytest.fixture
def escenario(make_planner, make_event, make_guest, auth_headers):
    duena = make_planner("duena@example.com")
    otra = make_planner("otra@example.com")
    event = make_event(duena)
    guest = make_guest(event)
    return event, guest, auth_headers(duena), auth_headers(otra)


EVENT_BODY = {
    "nombre": "Intento",
    "tipo": "otro",
    "fecha_hora": "2030-01-10T18:00",
    "lugar_nombre": "Salón",
    "direccion": "Tijuana",
    "fecha_limite_confirmacion": "2030-01-01T18:00",
}
GUEST_BODY = {"nombre_grupo": "Intruso", "lugares_asignados": 2}


def test_lista_solo_muestra_eventos_propios(client, escenario):
    event, _, duena, otra = escenario
    assert [item["id"] for item in client.get("/api/events", headers=duena).json()] == [event.id]
    assert client.get("/api/events", headers=otra).json() == []


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/api/events/{event}", None),
        ("put", "/api/events/{event}", EVENT_BODY),
        ("get", "/api/events/{event}/panel", None),
        ("get", "/api/events/{event}/export", None),
        ("post", "/api/events/{event}/guests", GUEST_BODY),
        ("put", "/api/events/{event}/guests/{guest}", GUEST_BODY),
        ("delete", "/api/events/{event}/guests/{guest}", None),
    ],
)
def test_otro_planner_recibe_404(client, escenario, method, path, body):
    event, guest, _, otra = escenario
    url = path.format(event=event.id, guest=guest.id)
    kwargs = {"json": body} if body else {}
    assert getattr(client, method)(url, headers=otra, **kwargs).status_code == 404


def test_otro_planner_no_puede_importar(client, escenario):
    event, _, _, otra = escenario
    response = client.post(
        f"/api/events/{event.id}/guests/import",
        headers=otra,
        files={"file": ("x.csv", b"nombre_grupo,telefono,lugares_asignados\nA,,2\n")},
    )
    assert response.status_code == 404


def test_invitado_de_otro_evento_no_se_alcanza_desde_evento_propio(
    client, make_event, escenario
):
    """Un invitado solo se alcanza desde la URL del evento al que pertenece."""
    event, guest, duena, _ = escenario
    otro_evento = make_event(event.planner, nombre="Otro evento")

    url = f"/api/events/{otro_evento.id}/guests/{guest.id}"
    assert client.delete(url, headers=duena).status_code == 404


@pytest.mark.parametrize("path", ["/api/events", "/api/events/1/panel"])
def test_sin_sesion_da_401(client, path):
    assert client.get(path).status_code == 401
