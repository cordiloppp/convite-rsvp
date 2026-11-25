from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("tipo IN ('boda', 'xv', 'cumpleaños', 'otro')", name="tipo_valido"),
        CheckConstraint("fecha_limite_confirmacion <= fecha_hora", name="limite_antes_del_evento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    planner_id: Mapped[int] = mapped_column(ForeignKey("planners.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lugar_nombre: Mapped[str] = mapped_column(String(200))
    direccion: Mapped[str] = mapped_column(String(300))
    link_mapa: Mapped[str | None] = mapped_column(String(500))
    mensaje: Mapped[str | None] = mapped_column(Text)
    imagen_portada_url: Mapped[str | None] = mapped_column(String(500))
    fecha_limite_confirmacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    planner: Mapped["Planner"] = relationship(back_populates="events")  # noqa: F821
    guests: Mapped[list["Guest"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan", passive_deletes=True
    )
