from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import GuestStatus
from app.security import generate_guest_token


class Guest(Base):
    """Una fila por familia o grupo invitado."""

    __tablename__ = "guests"
    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'confirmado', 'rechazado')", name="estado_valido"),
        CheckConstraint("lugares_asignados >= 1", name="asignados_positivos"),
        CheckConstraint(
            "lugares_confirmados >= 0 AND lugares_confirmados <= lugares_asignados",
            name="confirmados_en_rango",
        ),
        CheckConstraint(
            "(estado = 'confirmado' AND lugares_confirmados >= 1) "
            "OR (estado <> 'confirmado' AND lugares_confirmados = 0)",
            name="confirmados_segun_estado",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    nombre_grupo: Mapped[str] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(30))
    lugares_asignados: Mapped[int] = mapped_column(Integer)
    token: Mapped[str] = mapped_column(String(64), unique=True, default=generate_guest_token)
    estado: Mapped[str] = mapped_column(
        String(20), default=GuestStatus.PENDIENTE.value, server_default="pendiente"
    )
    lugares_confirmados: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    nota: Mapped[str | None] = mapped_column(Text)
    # Momento de la última respuesta del invitado, confirme o rechace.
    confirmado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    event: Mapped["Event"] = relationship(back_populates="guests")  # noqa: F821
