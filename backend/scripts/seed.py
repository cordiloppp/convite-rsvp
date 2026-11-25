"""Carga los datos de la demo.

Con SEED_DEMO=true solo actúa si el planner demo no existe, así que es seguro
ejecutarlo en cada arranque. Las fechas se calculan desde hoy para que la demo
siga vigente sin importar cuándo se levante.
"""
import random
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from urllib.parse import quote_plus

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Event, Guest, GuestStatus, Planner
from app.security import hash_password
from app.services.links import guest_link

DEMO_EMAIL = "demo@convite.mx"
DEMO_PASSWORD = "convite-demo-2026"

# Tokens fijos solo para los links de ejemplo del README. El resto son aleatorios.
TOKENS_EJEMPLO = {
    ("boda", "pendiente"): "demo-boda-pendiente",
    ("boda", "confirmado"): "demo-boda-confirmado",
    ("boda", "parcial"): "demo-boda-parcial",
    ("boda", "rechazado"): "demo-boda-rechazado",
    ("xv", "pendiente"): "demo-xv-pendiente",
}

NOTAS = (
    "Vamos con un bebé, ¿habrá silla alta?",
    "Una persona es vegetariana.",
    "Alergia a los mariscos en nuestra mesa, por favor.",
    "¡Muchas felicidades! Ahí estaremos.",
    "Llegamos desde San Diego, quizá un poco tarde por la garita.",
)
NOTAS_RECHAZO = (
    "Estaremos fuera de la ciudad, ¡que lo disfruten mucho!",
    "Lamentablemente no podremos acompañarlos. Un abrazo.",
)

BODA_GRUPOS = (
    ("Familia López Hernández", 4), ("Familia Ramírez Soto", 5), ("Padrinos Gómez Treviño", 2),
    ("Familia Castañeda", 4), ("Tíos Valenzuela", 3), ("Familia Ibarra Montes", 6),
    ("Sr. y Sra. Ochoa", 2), ("Familia Rentería", 4), ("Primos Zamora", 3),
    ("Familia Núñez Beltrán", 5), ("Compañeros de oficina de Eduardo", 6),
    ("Amigas de la universidad de Valeria", 5), ("Familia Cázares", 3), ("Tíos Armenta", 2),
    ("Familia Duarte Félix", 4), ("Sr. y Sra. Meza", 2), ("Familia Aguilar Rubio", 5),
    ("Familia Quintero", 3), ("Abuelos Salazar", 2), ("Familia Peña Lugo", 4),
    ("Primos Bojórquez", 3), ("Familia Estrada", 4), ("Sr. y Sra. Villaseñor", 2),
    ("Familia Corona Vega", 5), ("Familia Murillo", 3),
)

XV_GRUPOS = (
    ("Familia Sandoval Ruiz", 4), ("Padrinos Cervantes", 2), ("Familia Acosta", 5),
    ("Tíos Figueroa", 3), ("Familia Rosas Medina", 4), ("Amigas de la secundaria", 6),
    ("Familia Delgado", 3), ("Sr. y Sra. Carrillo", 2), ("Familia Montoya Ríos", 5),
    ("Primos Arellano", 4), ("Familia Guerrero", 3), ("Chambelanes y familias", 6),
    ("Familia Navarro Paz", 4), ("Abuelos Cisneros", 2), ("Familia Escobedo", 3),
    ("Tíos Lizárraga", 4), ("Familia Ponce", 5), ("Sr. y Sra. Rangel", 2),
    ("Familia Tapia Mora", 4), ("Familia Bustamante", 3), ("Primos Vizcarra", 3),
    ("Familia Salgado", 4), ("Maestras del Colegio Tijuana", 3), ("Familia Olvera", 2),
    ("Familia Trujillo", 5),
)


@dataclass(frozen=True)
class Plan:
    clave: str
    confirmados: int
    parciales: int
    rechazados: int


def _proximo_sabado(desde: datetime, dias_minimos: int, hora: time) -> datetime:
    fecha = desde.date() + timedelta(days=dias_minimos)
    fecha += timedelta(days=(5 - fecha.weekday()) % 7)
    return datetime.combine(fecha, hora, tzinfo=desde.tzinfo)


def _mapa(lugar: str, direccion: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(f'{lugar}, {direccion}')}"


def _telefono(rng: random.Random) -> str:
    # Clave de Tijuana (664) con prefijo 555, reservado para no tocar números reales.
    return f"664555{rng.randint(0, 9999):04d}"


def _agregar_invitados(
    event: Event,
    grupos: tuple[tuple[str, int], ...],
    plan: Plan,
    rng: random.Random,
    tokens: dict[tuple[str, str], str],
) -> None:
    orden = list(grupos)
    rng.shuffle(orden)
    ahora = datetime.now(UTC)

    for indice, (nombre, lugares) in enumerate(orden):
        guest = Guest(
            nombre_grupo=nombre, telefono=_telefono(rng), lugares_asignados=lugares
        )
        tipo = "pendiente"
        if indice < plan.confirmados:
            tipo = "confirmado"
            guest.estado = GuestStatus.CONFIRMADO.value
            parcial = indice < plan.parciales and lugares >= 2
            guest.lugares_confirmados = rng.randint(1, lugares - 1) if parcial else lugares
            if parcial:
                tipo = "parcial"
            guest.nota = rng.choice(NOTAS) if rng.random() < 0.35 else None
        elif indice < plan.confirmados + plan.rechazados:
            tipo = "rechazado"
            guest.estado = GuestStatus.RECHAZADO.value
            guest.nota = rng.choice(NOTAS_RECHAZO) if rng.random() < 0.5 else None

        if tipo != "pendiente":
            guest.confirmado_at = ahora - timedelta(hours=rng.randint(1, 24 * 12))

        token = tokens.pop((plan.clave, tipo), None)
        if token:
            guest.token = token
        event.guests.append(guest)


def seed() -> None:
    settings = get_settings()
    if not settings.seed_demo:
        return

    with SessionLocal() as db:
        if db.scalar(select(Planner).where(Planner.email == DEMO_EMAIL)):
            print("Seed: el planner demo ya existe, no se modifica nada.")
            return

        rng = random.Random(2026)
        ahora = datetime.now(settings.timezone)
        planner = Planner(
            nombre="Mariana Fuentes", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD)
        )

        boda_fecha = _proximo_sabado(ahora, 75, time(17, 0))
        boda_lugar = "Hacienda Valle de las Palmas"
        boda_direccion = "Blvd. Agua Caliente 4558, Col. Aviación, 22014 Tijuana, B.C."
        boda = Event(
            nombre="Boda Valeria & Eduardo",
            tipo="boda",
            fecha_hora=boda_fecha,
            lugar_nombre=boda_lugar,
            direccion=boda_direccion,
            link_mapa=_mapa(boda_lugar, boda_direccion),
            mensaje=(
                "Con la bendición de Dios y de nuestros padres, tenemos el honor de "
                "invitarlos a celebrar nuestra unión. Su presencia hará este día "
                "aún más especial."
            ),
            imagen_portada_url="/portadas/boda.svg",
            fecha_limite_confirmacion=boda_fecha - timedelta(days=21),
        )

        xv_fecha = _proximo_sabado(ahora, 45, time(19, 30))
        xv_lugar = "Terraza del Mar"
        xv_direccion = "Paseo Ensenada 1200, Playas de Tijuana, 22500 Tijuana, B.C."
        xv = Event(
            nombre="XV años de Regina",
            tipo="xv",
            fecha_hora=xv_fecha,
            lugar_nombre=xv_lugar,
            direccion=xv_direccion,
            link_mapa=_mapa(xv_lugar, xv_direccion),
            mensaje=(
                "Quince años de sueños, risas y momentos inolvidables. Acompáñenme a "
                "celebrar esta noche tan importante junto a mis papás."
            ),
            imagen_portada_url="/portadas/xv.svg",
            fecha_limite_confirmacion=xv_fecha - timedelta(days=14),
        )

        tokens = dict(TOKENS_EJEMPLO)
        _agregar_invitados(boda, BODA_GRUPOS, Plan("boda", 13, 3, 4), rng, tokens)
        _agregar_invitados(xv, XV_GRUPOS, Plan("xv", 11, 2, 5), rng, tokens)
        planner.events.extend([boda, xv])
        db.add(planner)
        db.commit()

        print(f"Seed: planner demo creado ({DEMO_EMAIL}).")
        for guest in (*boda.guests, *xv.guests):
            if guest.token.startswith("demo-"):
                print(f"  {guest.nombre_grupo} ({guest.estado}): {guest_link(guest.token)}")


if __name__ == "__main__":
    seed()
