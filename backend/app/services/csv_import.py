import csv
import io
from collections.abc import Iterable

from pydantic import ValidationError

from app.schemas.common import first_validation_message
from app.schemas.guest import GuestIn, ImportRowError

COLUMNAS = ("nombre_grupo", "telefono", "lugares_asignados")
MAX_FILAS = 5000


class CsvInvalido(Exception):
    """El archivo completo no se puede procesar."""


def _decode(content: bytes) -> str:
    # Excel en español suele guardar en Windows-1252; utf-8-sig cubre "CSV UTF-8".
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1252", errors="replace")


def _delimiter(text: str) -> str:
    header = next((line for line in text.splitlines() if line.strip()), "")
    return ";" if header.count(";") > header.count(",") else ","


def parse_guests_csv(
    content: bytes, existing_names: Iterable[str]
) -> tuple[list[GuestIn], list[ImportRowError]]:
    """Separa las filas válidas de las inválidas. Una fila mala no detiene el resto."""
    text = _decode(content)
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=_delimiter(text))

    try:
        reader.fieldnames = [(name or "").strip().lower() for name in reader.fieldnames or []]
    except csv.Error as exc:
        raise CsvInvalido("No se pudo leer el archivo CSV") from exc
    faltantes = [columna for columna in COLUMNAS if columna not in reader.fieldnames]
    if faltantes:
        raise CsvInvalido(f"Faltan columnas: {', '.join(faltantes)}")

    guests: list[GuestIn] = []
    errors: list[ImportRowError] = []
    seen = {name.casefold() for name in existing_names}

    try:
        for row in reader:
            values = {columna: (row.get(columna) or "").strip() for columna in COLUMNAS}
            if not any(values.values()):
                continue
            if len(guests) + len(errors) >= MAX_FILAS:
                raise CsvInvalido(f"El archivo supera el máximo de {MAX_FILAS} filas")
            try:
                guest = GuestIn(**values)
            except ValidationError as exc:
                mensaje = first_validation_message(exc.errors())
                errors.append(ImportRowError(fila=reader.line_num, mensaje=mensaje))
                continue
            key = guest.nombre_grupo.casefold()
            if key in seen:
                errors.append(
                    ImportRowError(fila=reader.line_num, mensaje="Ya existe un grupo con ese nombre")
                )
                continue
            seen.add(key)
            guests.append(guest)
    except csv.Error as exc:
        raise CsvInvalido("No se pudo leer el archivo CSV") from exc

    return guests, errors
