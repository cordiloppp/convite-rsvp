import io

import pytest
from openpyxl import load_workbook


@pytest.fixture
def evento(make_planner, make_event, auth_headers):
    planner = make_planner()
    return make_event(planner), auth_headers(planner)


def _importar(client, evento, content: bytes):
    event, headers = evento
    return client.post(
        f"/api/events/{event.id}/guests/import",
        headers=headers,
        files={"file": ("invitados.csv", content, "text/csv")},
    )


def _nombres(client, evento) -> list[str]:
    event, headers = evento
    panel = client.get(f"/api/events/{event.id}/panel", headers=headers).json()
    return [guest["nombre_grupo"] for guest in panel["guests"]]


def test_importa_csv_con_coma(client, evento):
    csv = "nombre_grupo,telefono,lugares_asignados\nFamilia López,6645550101,4\nTíos Ruiz,,2\n"
    response = _importar(client, evento, csv.encode("utf-8"))

    assert response.status_code == 200
    assert response.json() == {"importados": 2, "errores": []}
    assert _nombres(client, evento) == ["Familia López", "Tíos Ruiz"]


def test_importa_csv_de_excel_con_punto_y_coma_y_bom(client, evento):
    csv = "﻿Nombre_Grupo;Telefono;Lugares_Asignados\r\nFamilia Peña;6645550101;4\r\n;;\r\n"
    response = _importar(client, evento, csv.encode("utf-8"))

    assert response.json() == {"importados": 1, "errores": []}
    assert _nombres(client, evento) == ["Familia Peña"]


def test_importa_csv_en_windows_1252(client, evento):
    csv = "nombre_grupo;telefono;lugares_asignados\nFamilia Muñoz;;3\n"
    assert _importar(client, evento, csv.encode("cp1252")).json()["importados"] == 1
    assert _nombres(client, evento) == ["Familia Muñoz"]


def test_filas_invalidas_se_reportan_y_las_validas_se_importan(client, evento):
    csv = (
        "nombre_grupo,telefono,lugares_asignados\n"
        "Familia Buena,6645550101,4\n"
        ",6645550102,2\n"
        "Familia Cero,6645550103,0\n"
        "Familia Texto,6645550104,muchos\n"
        "Familia Tel,abc,2\n"
        "Otra Buena,,1\n"
    )
    data = _importar(client, evento, csv.encode("utf-8")).json()

    assert data["importados"] == 2
    assert [error["fila"] for error in data["errores"]] == [3, 4, 5, 6]
    assert "obligatorio" in data["errores"][0]["mensaje"]
    assert "entre 1 y" in data["errores"][1]["mensaje"]
    assert "número entero" in data["errores"][2]["mensaje"]
    assert "teléfono" in data["errores"][3]["mensaje"]
    assert _nombres(client, evento) == ["Familia Buena", "Otra Buena"]


def test_reimportar_no_duplica_grupos(client, evento):
    csv = "nombre_grupo,telefono,lugares_asignados\nFamilia López,,4\nfamilia lópez,,2\n".encode()
    primera = _importar(client, evento, csv).json()
    assert primera["importados"] == 1
    assert "Ya existe" in primera["errores"][0]["mensaje"]

    segunda = _importar(client, evento, csv).json()
    assert segunda["importados"] == 0
    assert _nombres(client, evento) == ["Familia López"]


@pytest.mark.parametrize(
    "contenido", [b"", b"nombre,lugares\nA,2\n", "sólo texto".encode("utf-8")]
)
def test_csv_sin_columnas_requeridas_da_400(client, evento, contenido):
    response = _importar(client, evento, contenido)
    assert response.status_code == 400
    assert "Faltan columnas" in response.json()["detail"]


def test_archivo_demasiado_grande_da_413(client, evento):
    assert _importar(client, evento, b"x" * (2 * 1024 * 1024 + 1)).status_code == 413


def test_exporta_excel_con_estado_y_resumen(client, evento, make_guest):
    event, headers = evento
    make_guest(event, "Familia Parcial", 5, estado="confirmado", lugares_confirmados=3, nota="Hola")
    make_guest(event, "Familia Rechazo", 2, estado="rechazado")
    make_guest(event, "Familia Pendiente", 4)

    response = client.get(f"/api/events/{event.id}/export", headers=headers)

    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert "invitados-boda-de-prueba.xlsx" in response.headers["content-disposition"]

    workbook = load_workbook(io.BytesIO(response.content))
    rows = list(workbook["Invitados"].iter_rows(values_only=True))
    assert rows[0][:6] == (
        "Grupo",
        "Teléfono",
        "Lugares asignados",
        "Estado",
        "Lugares confirmados",
        "Lugares que no asistirán",
    )
    por_grupo = {row[0]: row for row in rows[1:]}
    assert por_grupo["Familia Parcial"][2:6] == (5, "Confirmado", 3, 2)
    assert por_grupo["Familia Rechazo"][2:6] == (2, "Rechazado", 0, 2)
    assert por_grupo["Familia Pendiente"][2:6] == (4, "Pendiente", 0, 0)

    resumen = {row[0]: row[1] for row in workbook["Resumen"].iter_rows(values_only=True)}
    assert resumen["Confirmados"] == 3
    assert resumen["No asistirán"] == 4
    assert resumen["Pendientes"] == 4


def test_texto_del_invitado_no_se_exporta_como_formula(client, evento, make_guest):
    event, headers = evento
    formula = '=HYPERLINK("http://malo.example","clic")'
    make_guest(event, formula, 2, estado="rechazado", nota=formula)

    response = client.get(f"/api/events/{event.id}/export", headers=headers)

    sheet = load_workbook(io.BytesIO(response.content))["Invitados"]
    assert sheet["A2"].data_type == "s"
    assert sheet["G2"].data_type == "s"
