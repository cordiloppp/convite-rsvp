import io
from collections.abc import Sequence

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from app.config import get_settings
from app.models import Event, Guest, GuestStatus
from app.schemas.event import Resumen
from app.services.links import guest_link

ESTADOS = {
    GuestStatus.PENDIENTE.value: "Pendiente",
    GuestStatus.CONFIRMADO.value: "Confirmado",
    GuestStatus.RECHAZADO.value: "Rechazado",
}

COLUMNAS: tuple[tuple[str, int], ...] = (
    ("Grupo", 32),
    ("Teléfono", 18),
    ("Lugares asignados", 18),
    ("Estado", 14),
    ("Lugares confirmados", 20),
    ("Lugares que no asistirán", 24),
    ("Nota", 40),
    ("Fecha de respuesta", 20),
    ("Link de invitación", 60),
)


def _text(sheet: Worksheet, row: int, column: int, value: str | None) -> None:
    # Se fuerza tipo texto: lo que escribe un invitado o trae un CSV (por ejemplo
    # "=HYPERLINK(...)") no debe ejecutarse como fórmula al abrir el archivo.
    cell = sheet.cell(row=row, column=column)
    cell.value = value
    if value is not None:
        cell.data_type = "s"


def _no_asistiran(guest: Guest) -> int:
    if guest.estado == GuestStatus.PENDIENTE.value:
        return 0
    return guest.lugares_asignados - guest.lugares_confirmados


def build_workbook(event: Event, guests: Sequence[Guest], resumen: Resumen) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Invitados"

    for column, (titulo, ancho) in enumerate(COLUMNAS, start=1):
        cell = sheet.cell(row=1, column=column, value=titulo)
        cell.font = Font(bold=True)
        sheet.column_dimensions[cell.column_letter].width = ancho
    sheet.freeze_panes = "A2"

    timezone = get_settings().timezone
    for row, guest in enumerate(guests, start=2):
        _text(sheet, row, 1, guest.nombre_grupo)
        _text(sheet, row, 2, guest.telefono)
        sheet.cell(row=row, column=3, value=guest.lugares_asignados)
        _text(sheet, row, 4, ESTADOS[guest.estado])
        sheet.cell(row=row, column=5, value=guest.lugares_confirmados)
        sheet.cell(row=row, column=6, value=_no_asistiran(guest))
        _text(sheet, row, 7, guest.nota)
        if guest.confirmado_at:
            local = guest.confirmado_at.astimezone(timezone).replace(tzinfo=None)
            cell = sheet.cell(row=row, column=8, value=local)
            cell.number_format = "yyyy-mm-dd hh:mm"
        _text(sheet, row, 9, guest_link(guest.token))
    sheet.auto_filter.ref = sheet.dimensions

    summary = workbook.create_sheet("Resumen")
    summary.column_dimensions["A"].width = 30
    _text(summary, 1, 1, event.nombre)
    summary["A1"].font = Font(bold=True, size=14)
    filas = (
        ("Lugares asignados", resumen.lugares_total),
        ("Confirmados", resumen.lugares_confirmados),
        ("No asistirán", resumen.lugares_no_asistiran),
        ("Pendientes", resumen.lugares_pendientes),
        (None, None),
        ("Familias que confirmaron", resumen.familias_confirmadas),
        ("Familias que rechazaron", resumen.familias_rechazadas),
        ("Familias pendientes", resumen.familias_pendientes),
    )
    for row, (etiqueta, valor) in enumerate(filas, start=3):
        summary.cell(row=row, column=1, value=etiqueta)
        summary.cell(row=row, column=2, value=valor)

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()
