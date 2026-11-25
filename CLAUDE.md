# Convite: arranque tras reiniciar

Demo de invitaciones digitales con RSVP. Ver `README.md` para el producto.

**Estado:** el código de las 6 etapas está terminado. Se probó con Python y PostgreSQL temporales (pytest 62/62, navegador 33/33). `docker compose up` **nunca se ha ejecutado**. Docker Desktop ya está instalado, pero hacía falta reiniciar Windows.

Si el usuario pide arrancar o verificar la demo, o dice "listo", sigue estos pasos en orden y repórtale el resultado en español.

## 1. Comprobar Docker

- En la terminal puede que `docker` no esté en el PATH. Si falla, usa `C:\Program Files\Docker\Docker\resources\bin\docker.exe`.
- Ejecuta `docker version`. Si no aparece la sección Server, el motor no está corriendo: abre `C:\Program Files\Docker\Docker\Docker Desktop.exe` y espera hasta 2 minutos a que responda.
- Si sigue sin responder:
  - Comprueba que Windows se reinició: `(Get-CimInstance Win32_OperatingSystem).LastBootUpTime` debe ser posterior al 2026-11-05 20:15. Si no, pide al usuario que reinicie y detente.
  - Docker Desktop pide aceptar sus términos la primera vez. Debe hacerlo el usuario: no los aceptes por él. Pídeselo y espera.
  - Si el error menciona WSL, pide o ejecuta `wsl --update`. No reinicies la computadora por tu cuenta.

## 2. Levantar

Desde la raíz del proyecto. `.env` ya existe; si falta, cópialo de `.env.example`.

```powershell
docker compose up -d --build
docker compose ps
```

La primera construcción tarda varios minutos: ejecútala en segundo plano. Los tres servicios deben quedar en marcha, y `db` y `backend` como `healthy`. Si algo falla, lee `docker compose logs backend` o el servicio afectado.

## 3. Verificar

**Servicios**
- http://localhost:5173 responde 200.
- http://localhost:5173/api/health devuelve `{"status":"ok"}`. Esto comprueba nginx hasta el backend.
- http://localhost:5173/i/demo-boda-pendiente devuelve el HTML de la app, no un 404 de nginx.
- `docker compose logs backend` muestra `Seed: planner demo creado`.

**Pruebas del backend** (se esperan 62)
```powershell
docker compose exec backend pytest
```

**Prueba de navegador** (se esperan 33 comprobaciones y 0 errores de consola)

Modifica datos: elimina invitados y crea un evento. Necesita el seed recién cargado, así que córrela una sola vez sobre la base limpia. Para repetirla hay que reiniciar los datos con `docker compose down -v`, que **borra la base**. Si el usuario ya creó datos propios, pregúntale antes.

```powershell
cd e2e
npm install
npx playwright install chromium
npm test
```

Las capturas quedan en `e2e/shots/`. Revísalas: la suite no detecta defectos visuales.

## 4. Reportar

Di qué pasó y qué no, con los números reales. Si todo pasa, entrega al usuario:
- App: http://localhost:5173
- Login: `demo@convite.mx` / `convite-demo-2026`
- Invitación de ejemplo: http://localhost:5173/i/demo-boda-pendiente

Después de la prueba de navegador los datos quedan alterados. Ofrece dejar la demo limpia con `docker compose down -v` y `docker compose up -d`.

## Dónde es más probable que falle

Esto no se ha probado nunca:
- Construcción de las imágenes. `npm ci` usa un lockfile generado en Windows; ya incluye los binarios de Linux.
- nginx: proxy de `/api`, rutas de React y `frontend/nginx.conf`.
- PostgreSQL 16: las pruebas corrieron en la 18.
- Saltos de línea CRLF en archivos que lea Linux.

## Notas de trabajo

- Windows 10 Home. Git Bash falla con heredocs largos: escribe los archivos con Write.
- Decisiones del usuario que no deben cambiar: las categorías del resumen son Confirmados, No asistirán y Pendientes. Nunca llames "rechazados" a los lugares de "No asistirán". Las confirmaciones parciales se muestran como "3 de 5".
- Fuera de alcance: QR de entrada, mesas, recordatorios, pagos y galería.
