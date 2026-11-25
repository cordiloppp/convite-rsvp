from app.models import Guest

RSVP = "/api/public/invitations/{}/rsvp"
INVITATION = "/api/public/invitations/{}"


def _guest(make_planner, make_event, make_guest, limite_en_dias=20, lugares=4) -> Guest:
    event = make_event(make_planner(), limite_en_dias=limite_en_dias)
    return make_guest(event, lugares=lugares, telefono="6645550101")


def test_invitacion_publica_no_expone_datos_privados(client, make_planner, make_event, make_guest):
    guest = _guest(make_planner, make_event, make_guest)
    response = client.get(INVITATION.format(guest.token))

    assert response.status_code == 200
    data = response.json()
    assert data["guest"]["nombre_grupo"] == "Familia López"
    assert data["puede_responder"] is True
    assert data["marca"]["nombre"]
    assert data["event"]["link_mapa"].startswith("https://www.google.com/maps/")
    assert "telefono" not in data["guest"]
    assert "6645550101" not in response.text
    assert "planner_id" not in data["event"]


def test_token_inexistente_da_404_amable(client):
    response = client.get(INVITATION.format("no-existe"))
    assert response.status_code == 404
    assert response.json()["detail"] == "Invitación no disponible"


def test_confirmar_guarda_lugares_y_nota(client, db, make_planner, make_event, make_guest):
    guest = _guest(make_planner, make_event, make_guest)
    response = client.post(
        RSVP.format(guest.token), json={"asistira": True, "lugares": 3, "nota": "  Sin nueces  "}
    )

    assert response.status_code == 200
    db.refresh(guest)
    assert guest.estado == "confirmado"
    assert guest.lugares_confirmados == 3
    assert guest.nota == "Sin nueces"
    assert guest.confirmado_at is not None


def test_rechazar_deja_cero_lugares_aunque_envie_lugares(
    client, db, make_planner, make_event, make_guest
):
    guest = _guest(make_planner, make_event, make_guest)
    response = client.post(RSVP.format(guest.token), json={"asistira": False, "lugares": 3})

    assert response.status_code == 200
    db.refresh(guest)
    assert guest.estado == "rechazado"
    assert guest.lugares_confirmados == 0


def test_puede_cambiar_su_respuesta_antes_de_la_fecha_limite(
    client, db, make_planner, make_event, make_guest
):
    guest = _guest(make_planner, make_event, make_guest)
    client.post(RSVP.format(guest.token), json={"asistira": True, "lugares": 4})
    assert client.post(RSVP.format(guest.token), json={"asistira": False}).status_code == 200
    assert client.post(
        RSVP.format(guest.token), json={"asistira": True, "lugares": 2}
    ).status_code == 200

    db.refresh(guest)
    assert (guest.estado, guest.lugares_confirmados) == ("confirmado", 2)


def test_no_se_puede_confirmar_mas_de_lo_asignado(
    client, db, make_planner, make_event, make_guest
):
    guest = _guest(make_planner, make_event, make_guest, lugares=4)
    response = client.post(RSVP.format(guest.token), json={"asistira": True, "lugares": 5})

    assert response.status_code == 422
    assert response.json()["detail"] == "Puedes confirmar de 1 a 4 lugares"
    db.refresh(guest)
    assert (guest.estado, guest.lugares_confirmados) == ("pendiente", 0)


def test_confirmar_exige_al_menos_un_lugar(client, make_planner, make_event, make_guest):
    guest = _guest(make_planner, make_event, make_guest)
    for body in ({"asistira": True}, {"asistira": True, "lugares": 0}):
        assert client.post(RSVP.format(guest.token), json=body).status_code == 422


def test_despues_de_la_fecha_limite_es_solo_lectura(
    client, db, make_planner, make_event, make_guest
):
    guest = _guest(make_planner, make_event, make_guest, limite_en_dias=-1)
    assert client.get(INVITATION.format(guest.token)).json()["puede_responder"] is False

    response = client.post(RSVP.format(guest.token), json={"asistira": True, "lugares": 2})

    assert response.status_code == 403
    db.refresh(guest)
    assert guest.estado == "pendiente"


def test_link_deja_de_funcionar_al_eliminar_invitado(
    client, make_planner, make_event, make_guest, auth_headers
):
    planner = make_planner()
    event = make_event(planner)
    guest = make_guest(event)
    client.post(RSVP.format(guest.token), json={"asistira": True, "lugares": 2})

    deleted = client.delete(
        f"/api/events/{event.id}/guests/{guest.id}", headers=auth_headers(planner)
    )

    assert deleted.status_code == 204
    assert client.get(INVITATION.format(guest.token)).status_code == 404
    assert client.post(RSVP.format(guest.token), json={"asistira": False}).status_code == 404
