from enum import StrEnum


class EventType(StrEnum):
    BODA = "boda"
    XV = "xv"
    CUMPLEANOS = "cumpleaños"
    OTRO = "otro"


class GuestStatus(StrEnum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    RECHAZADO = "rechazado"
