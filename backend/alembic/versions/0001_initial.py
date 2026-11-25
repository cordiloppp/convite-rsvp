"""Esquema inicial: planners, events y guests

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "planners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("email", name="uq_planners_email"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("planner_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lugar_nombre", sa.String(200), nullable=False),
        sa.Column("direccion", sa.String(300), nullable=False),
        sa.Column("link_mapa", sa.String(500), nullable=True),
        sa.Column("mensaje", sa.Text(), nullable=True),
        sa.Column("imagen_portada_url", sa.String(500), nullable=True),
        sa.Column("fecha_limite_confirmacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["planner_id"],
            ["planners.id"],
            name="fk_events_planner_id_planners",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "tipo IN ('boda', 'xv', 'cumpleaños', 'otro')", name=op.f("ck_events_tipo_valido")
        ),
        sa.CheckConstraint(
            "fecha_limite_confirmacion <= fecha_hora", name=op.f("ck_events_limite_antes_del_evento")
        ),
    )
    op.create_index("ix_events_planner_id", "events", ["planner_id"])

    op.create_table(
        "guests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("nombre_grupo", sa.String(200), nullable=False),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("lugares_asignados", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("estado", sa.String(20), server_default="pendiente", nullable=False),
        sa.Column("lugares_confirmados", sa.Integer(), server_default="0", nullable=False),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name="fk_guests_event_id_events", ondelete="CASCADE"
        ),
        sa.UniqueConstraint("token", name="uq_guests_token"),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'confirmado', 'rechazado')", name=op.f("ck_guests_estado_valido")
        ),
        sa.CheckConstraint("lugares_asignados >= 1", name=op.f("ck_guests_asignados_positivos")),
        sa.CheckConstraint(
            "lugares_confirmados >= 0 AND lugares_confirmados <= lugares_asignados",
            name=op.f("ck_guests_confirmados_en_rango"),
        ),
        sa.CheckConstraint(
            "(estado = 'confirmado' AND lugares_confirmados >= 1) "
            "OR (estado <> 'confirmado' AND lugares_confirmados = 0)",
            name=op.f("ck_guests_confirmados_segun_estado"),
        ),
    )
    op.create_index("ix_guests_event_id", "guests", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_guests_event_id", table_name="guests")
    op.drop_table("guests")
    op.drop_index("ix_events_planner_id", table_name="events")
    op.drop_table("events")
    op.drop_table("planners")
