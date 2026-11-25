# Convite

Demo de una plataforma de invitaciones digitales con confirmación de asistencia (RSVP) para planners de eventos.

- **Planner:** inicia sesión, crea eventos, agrega invitados y sigue las confirmaciones.
- **Invitado:** no inicia sesión. Abre su link personalizado, ve la invitación y responde.

Stack: React + Vite + TypeScript + Tailwind, FastAPI + SQLAlchemy 2 + Alembic, y PostgreSQL.

## Cómo levantarlo

Necesitas Docker con Compose (en Windows, Docker Desktop con WSL2).

```bash
cp .env.example .env
docker compose up --build
```

En PowerShell, usa `Copy-Item .env.example .env` para el primer paso. Antes de usarlo fuera de tu máquina, cambia `POSTGRES_PASSWORD` y `JWT_SECRET` en `.env`.

Al arrancar se aplican las migraciones y se cargan los datos de ejemplo.

| Servicio | URL |
|---|---|
| Aplicación | http://localhost:5173 |
| Documentación de la API | http://localhost:8000/api/docs |

## Credenciales demo

| Email | Contraseña |
|---|---|
| `demo@convite.mx` | `convite-demo-2026` |

## Links de ejemplo

| Evento | Familia | Estado inicial | Link |
|---|---|---|---|
| Boda | Familia Quintero | Pendiente | http://localhost:5173/i/demo-boda-pendiente |
| Boda | Familia Ibarra Montes | Confirmada | http://localhost:5173/i/demo-boda-confirmado |
| Boda | Tíos Valenzuela | Confirmación parcial | http://localhost:5173/i/demo-boda-parcial |
| Boda | Familia Duarte Félix | Rechazó | http://localhost:5173/i/demo-boda-rechazado |
| XV años | Familia Ponce | Pendiente | http://localhost:5173/i/demo-xv-pendiente |

Esos cinco tokens son fijos y legibles solo para que este README tenga links estables. Todos los demás, y los de cualquier invitado nuevo, se generan con `secrets.token_urlsafe`.

## Qué probar

1. Abre un link pendiente, confirma y vuelve a abrirlo para cambiar tu respuesta.
2. Entra al panel y deja abierta la Boda. Responde desde otra ventana: el panel se actualiza solo en máximo 15 segundos.
3. **Solo lectura:** edita el evento y pon una fecha límite pasada. La invitación deja de aceptar respuestas.
4. **Eliminar:** borra una familia que ya confirmó. Verás una advertencia extra y su link mostrará "Invitación no disponible".
5. **Importar:** usa `frontend/public/ejemplo-invitados.csv`, que también se descarga desde el diálogo de importación.
6. **Exportar:** descarga el Excel, con una hoja de invitados y otra de resumen.

## Probar desde un teléfono

Con `localhost`, los links no abren desde otro dispositivo. Para probar en tu celular:

1. Conecta la computadora y el teléfono a la misma red.
2. En `.env`, pon `PUBLIC_APP_URL=http://TU_IP_LOCAL:5173`.
3. Recrea el backend para que tome el cambio: `docker compose up -d backend`.

Para enviar links reales por WhatsApp a otras personas, `PUBLIC_APP_URL` debe ser una URL pública, por ejemplo la de un túnel.

## Pruebas

```bash
docker compose exec backend pytest
```

Corren en una base `convite_test` que se crea y se borra sola, con las mismas migraciones de la aplicación. Cubren RSVP, límite de lugares, fecha límite, acceso entre planners, edición y eliminación de invitados, importación, exportación y seed.

`e2e/` contiene una prueba de navegador con Playwright. Modifica los datos, así que debe correr sobre un seed recién cargado:

```bash
cd e2e
npm install
npx playwright install chromium
npm test
```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Acceso a la base de datos |
| `JWT_SECRET` | Firma las sesiones. Mínimo 32 caracteres |
| `JWT_EXPIRE_MINUTES` | Duración de la sesión |
| `BRAND_NAME`, `BRAND_URL` | Marca del panel y del pie de las invitaciones |
| `PUBLIC_APP_URL` | Base de los links que reciben los invitados |
| `APP_TIMEZONE` | Zona horaria en la que se capturan y muestran las fechas |
| `SEED_DEMO` | Carga los datos de ejemplo si el planner demo no existe |

## Cómo se calcula el resumen

Los lugares se reparten en tres categorías que siempre suman el total asignado:

- **Confirmados:** lugares confirmados.
- **No asistirán:** lugares de familias que rechazaron, más los sobrantes de confirmaciones parciales.
- **Pendientes:** lugares de familias que no han respondido.

Aparte se muestra el conteo por familias. En la tabla, una confirmación parcial se marca como "3 de 5".

## Reglas de negocio

- `lugares_confirmados` nunca supera `lugares_asignados`: se valida en la API y con un `CHECK` en PostgreSQL.
- `lugares_asignados` no puede bajar de los lugares ya confirmados.
- La fecha límite se aplica en el backend, no solo en la pantalla.
- Un planner solo accede a sus propios eventos e invitados. Lo ajeno responde 404.
- Los números de 10 dígitos se tratan como mexicanos en WhatsApp (prefijo `52`).
- El CSV acepta coma o punto y coma, y archivos UTF-8 o Windows-1252 guardados desde Excel. Las filas válidas se importan, las inválidas se reportan y los nombres repetidos se omiten.
- Los textos exportados a Excel se guardan como texto, para que no se ejecuten como fórmulas.

## Estructura

```
backend/
  alembic/          migraciones
  app/
    models/         planners, events, guests
    schemas/        validación y respuestas
    routers/        auth, events, guests, public
    services/       rsvp, resumen, links, CSV, Excel
  scripts/seed.py   datos de ejemplo
  tests/
frontend/
  public/           portadas y CSV de ejemplo
  src/
    api/            cliente y tipos
    components/     interfaz compartida
    hooks/          polling y configuración
    pages/public/   invitación
    pages/planner/  login, eventos y panel
```

## Reiniciar la demo

```bash
docker compose down -v
docker compose up --build
```

`-v` borra la base de datos, incluidos los eventos que hayas creado. Las fechas del seed se calculan a partir del día en que se ejecuta, y los nombres, lugares y direcciones son ficticios.

## Fuera de alcance

Esta demo no incluye QR de entrada, asignación de mesas, recordatorios automáticos, pagos ni galería de fotos. Tampoco tiene registro público de planners ni subida de imágenes: la portada se indica con una URL.
