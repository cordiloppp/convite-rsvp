from urllib.parse import unquote

import pytest

from app.services.links import whatsapp_number


def _body(**cambios):
    return {
        "nombre": "XV de Regina",
        "tipo": "xv",
        "fecha_hora": "2030-05-10T19:00",
        "lugar_nombre": "Salón Terraza",
        "direccion": "Playas de Tijuana",
        "fecha_limite_confirmacion": "2030-04-30T23:59",
    } | cambios


def test_crear_y_editar_evento(client, make_planner, auth_headers):
    headers = auth_headers(make_planner())
    created = client.post("/api/events", json=_body(), headers=headers)
    assert created.status_code == 201
    event = created.json()
    # Sin zona horaria, la fecha se interpreta en hora de Tijuana (PDT en mayo).
    assert event["fecha_hora"] == "2030-05-10T19:00:00-07:00"

    updated = client.put(
        f"/api/events/{event['id']}", json=_body(lugar_nombre="Otro salón"), headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["lugar_nombre"] == "Otro salón"


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"fecha_limite_confirmacion": "2030-06-01T00:00"}, "posterior al evento"),
        ({"link_mapa": "javascript:alert(1)"}, "http"),
        ({"imagen_portada_url": "javascript:alert(1)"}, "http"),
        ({"nombre": "   "}, "obligatorio"),
    ],
)
def test_evento_invalido_da_mensaje_en_espanol(client, make_planner, auth_headers, cambio, mensaje):
    response = client.post("/api/events", json=_body(**cambio), headers=auth_headers(make_planner()))
    assert response.status_code == 422
    assert mensaje in response.json()["detail"]


def test_portada_acepta_ruta_local_y_url(client, make_planner, auth_headers):
    headers = auth_headers(make_planner())
    for url in ("/portadas/boda.svg", "https://ejemplo.mx/foto.jpg"):
        body = _body(imagen_portada_url=url)
        assert client.post("/api/events", json=body, headers=headers).status_code == 201


def test_resumen_separa_no_asistiran_de_rechazos(
    client, make_planner, make_event, make_guest, auth_headers
):
    planner = make_planner()
    event = make_event(planner)
    make_guest(event, "Parcial", 5, estado="confirmado", lugares_confirmados=3)
    make_guest(event, "Completa", 2, estado="confirmado", lugares_confirmados=2)
    make_guest(event, "Rechazo", 4, estado="rechazado")
    make_guest(event, "Pendiente", 6)

    resumen = client.get(
        f"/api/events/{event.id}/panel", headers=auth_headers(planner)
    ).json()["resumen"]

    assert resumen == {
        "lugares_total": 17,
        "lugares_confirmados": 5,
        "lugares_no_asistiran": 6,  # 4 del rechazo + 2 sobrantes de la parcial
        "lugares_pendientes": 6,
        "familias_total": 4,
        "familias_confirmadas": 2,
        "familias_rechazadas": 1,
        "familias_pendientes": 1,
    }


def test_panel_de_evento_sin_invitados(client, make_planner, make_event, auth_headers):
    planner = make_planner()
    event = make_event(planner)
    panel = client.get(f"/api/events/{event.id}/panel", headers=auth_headers(planner)).json()
    assert panel["guests"] == []
    assert panel["resumen"]["lugares_total"] == 0


def test_invitado_tiene_link_y_whatsapp(client, make_planner, make_event, auth_headers):
    planner = make_planner()
    event = make_event(planner)
    guest = client.post(
        f"/api/events/{event.id}/guests",
        json={"nombre_grupo": "Familia Ruiz", "telefono": "664 555 0101", "lugares_asignados": 3},
        headers=auth_headers(planner),
    ).json()

    assert len(guest["token"]) >= 40
    assert guest["link"].endswith(f"/i/{guest['token']}")
    assert guest["whatsapp_url"].startswith("https://wa.me/526645550101?text=")
    assert guest["link"] in unquote(guest["whatsapp_url"])
    assert "Familia Ruiz" in unquote(guest["whatsapp_url"])


def test_invitado_sin_telefono_no_tiene_whatsapp(client, make_planner, make_event, auth_headers):
    planner = make_planner()
    event = make_event(planner)
    guest = client.post(
        f"/api/events/{event.id}/guests",
        json={"nombre_grupo": "Sin teléfono", "lugares_asignados": 1},
        headers=auth_headers(planner),
    ).json()
    assert guest["whatsapp_url"] is None


@pytest.mark.parametrize(
    ("telefono", "esperado"),
    [
        ("6645550101", "526645550101"),
        ("+52 664 555 0101", "526645550101"),
        ("(664) 555-0101", "526645550101"),
        ("+1 619 555 0101", "16195550101"),
        ("", None),
        (None, None),
        ("12345", None),
    ],
)
def test_normaliza_numero_de_whatsapp(telefono, esperado):
    assert whatsapp_number(telefono) == esperado


def test_no_se_puede_bajar_asignados_por_debajo_de_confirmados(
    client, db, make_planner, make_event, make_guest, auth_headers
):
    planner = make_planner()
    event = make_event(planner)
    guest = make_guest(event, lugares=5, estado="confirmado", lugares_confirmados=3)
    url = f"/api/events/{event.id}/guests/{guest.id}"
    headers = auth_headers(planner)

    rejected = client.put(
        url, json={"nombre_grupo": "Familia López", "lugares_asignados": 2}, headers=headers
    )
    assert rejected.status_code == 409
    assert "ya confirmó 3" in rejected.json()["detail"]
    db.refresh(guest)
    assert guest.lugares_asignados == 5

    accepted = client.put(
        url, json={"nombre_grupo": "Familia López", "lugares_asignados": 3}, headers=headers
    )
    assert accepted.status_code == 200
    assert accepted.json()["estado"] == "confirmado"
    assert accepted.json()["token"] == guest.token


@pytest.mark.parametrize(
    ("body", "mensaje"),
    [
        ({"nombre_grupo": "A", "lugares_asignados": 0}, "entre 1 y"),
        ({"nombre_grupo": "A", "lugares_asignados": "dos"}, "número entero"),
        ({"nombre_grupo": " ", "lugares_asignados": 1}, "obligatorio"),
        ({"nombre_grupo": "A", "telefono": "abc", "lugares_asignados": 1}, "teléfono"),
    ],
)
def test_invitado_invalido(client, make_planner, make_event, auth_headers, body, mensaje):
    planner = make_planner()
    event = make_event(planner)
    response = client.post(
        f"/api/events/{event.id}/guests", json=body, headers=auth_headers(planner)
    )
    assert response.status_code == 422
    assert mensaje in response.json()["detail"]
