import { chromium, devices } from "playwright";
import fs from "node:fs";

const BASE = process.env.BASE ?? "http://localhost:5173";
const SHOTS = new URL("./shots/", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");
fs.mkdirSync(SHOTS, { recursive: true });
const results = [];
const consoleErrors = [];

async function check(name, fn) {
  try {
    await fn();
    results.push(["OK ", name]);
    console.log("OK  ", name);
  } catch (error) {
    results.push(["FAIL", name]);
    console.log("FAIL", name, "\n     ", String(error.message).split("\n").slice(0, 3).join(" | "));
  }
}
const eq = (a, b, label = "") => {
  if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${label} esperado ${JSON.stringify(b)}, obtuve ${JSON.stringify(a)}`);
};
const ok = (value, label) => {
  if (!value) throw new Error(label);
};
const watch = (page, label) => {
  page.on("console", (m) => m.type() === "error" && consoleErrors.push(`${label}: ${m.text()}`));
  page.on("pageerror", (e) => consoleErrors.push(`${label}: ${e.message}`));
};
const noHScroll = (page) =>
  page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth);
const summaryNumbers = async (page) => {
  const text = await page.getByLabel("Resumen de confirmaciones").innerText();
  const pick = (label) => Number(text.match(new RegExp(`${label}\\s+(\\d+)`))[1]);
  return {
    total: pick("Lugares asignados"),
    conf: pick("Confirmados"),
    no: pick("No asistirán"),
    pend: pick("Pendientes"),
  };
};

const browser = await chromium.launch();

// ---------- INVITADO EN TELEFONO ----------
const phone = await browser.newContext({ ...devices["iPhone 13"], timezoneId: "America/Tijuana", locale: "es-MX" });
const inv = await phone.newPage();
watch(inv, "invitado");

await inv.goto(`${BASE}/i/demo-boda-pendiente`);
await check("invitación: saludo con familia y lugares", async () => {
  await inv.getByText(/Hola Familia Quintero, tienen 3 lugares reservados/).waitFor({ timeout: 5000 });
});
await check("invitación: portada carga", async () => {
  await inv.waitForFunction(() => { const i = document.querySelector("img"); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 5000 });
});
await check("invitación: nombre, fecha en texto y cuenta regresiva viva", async () => {
  await inv.getByRole("heading", { name: "Boda Valeria & Eduardo" }).waitFor();
  const body = await inv.locator("body").innerText();
  ok(/sábado/i.test(body), "no aparece el día sábado");
  const timer = inv.getByRole("timer");
  const first = await timer.innerText();
  await inv.waitForTimeout(1300);
  ok(first !== (await timer.innerText()), "la cuenta regresiva no avanza");
});
await check("invitación: botón de Maps y pie con marca", async () => {
  const href = await inv.getByRole("link", { name: "Ver en Google Maps" }).getAttribute("href");
  ok(href.startsWith("https://www.google.com/maps/"), href);
  const brand = inv.getByRole("link", { name: "Convite" });
  ok(await inv.getByText("Invitación hecha por").isVisible(), "sin pie");
  ok((await brand.getAttribute("href")).startsWith("https://"), "BRAND_URL");
});
await check("invitación: móvil sin scroll horizontal", async () => ok(await noHScroll(inv), "hay scroll horizontal"));
await inv.screenshot({ path: `${SHOTS}01-invitacion-movil.png`, fullPage: true });

await check("RSVP: selector ofrece solo de 1 a 3 lugares", async () => {
  await inv.getByText("Sí, asistiremos").click();
  eq(await inv.getByRole("combobox").locator("option").count(), 3, "opciones");
});
await check("RSVP: confirmación parcial lleva a agradecimiento", async () => {
  await inv.getByRole("combobox").selectOption("2");
  await inv.getByRole("textbox").fill("Sin mariscos, por favor");
  await inv.screenshot({ path: `${SHOTS}02-formulario-rsvp.png`, fullPage: true });
  await inv.getByRole("button", { name: "Enviar respuesta" }).click();
  await inv.getByRole("heading", { name: "¡Gracias!" }).waitFor({ timeout: 5000 });
  await inv.getByText("Confirmaron 2 de 3 lugares").waitFor();
  await inv.screenshot({ path: `${SHOTS}03-agradecimiento.png` });
});
await check("RSVP: al recargar conserva la respuesta y deja cambiarla", async () => {
  await inv.reload();
  await inv.getByText("Confirmaron 2 de 3 lugares.").waitFor({ timeout: 5000 });
  await inv.getByRole("button", { name: "Cambiar mi respuesta" }).click();
  eq(await inv.getByRole("combobox").inputValue(), "2", "lugares precargados");
  await inv.getByText("No podremos ir").click();
  await inv.getByRole("button", { name: "Enviar respuesta" }).click();
  await inv.getByRole("heading", { name: "Gracias por avisarnos" }).waitFor({ timeout: 5000 });
});
await check("link inválido: mensaje amable", async () => {
  await inv.goto(`${BASE}/i/token-que-no-existe`);
  await inv.getByRole("heading", { name: "Invitación no disponible" }).waitFor({ timeout: 5000 });
  await inv.screenshot({ path: `${SHOTS}04-no-disponible.png` });
});

// ---------- PLANNER (navegador en otra zona horaria) ----------
const desktop = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  timezoneId: "America/New_York",
  locale: "es-MX",
  acceptDownloads: true,
  permissions: ["clipboard-read", "clipboard-write"],
});
const p = await desktop.newPage();
watch(p, "planner");

await check("acceso: sin sesión redirige a login", async () => {
  await p.goto(`${BASE}/`);
  await p.waitForURL("**/login", { timeout: 5000 });
});
await check("login: credenciales malas muestran error", async () => {
  await p.getByLabel("Email").fill("demo@convite.mx");
  await p.getByLabel("Contraseña").fill("mala");
  await p.getByRole("button", { name: "Entrar" }).click();
  await p.getByText("Email o contraseña incorrectos").waitFor({ timeout: 5000 });
  await p.screenshot({ path: `${SHOTS}05-login.png` });
});
await check("login: credenciales demo entran y listan 2 eventos", async () => {
  await p.getByLabel("Contraseña").fill("convite-demo-2026");
  await p.getByRole("button", { name: "Entrar" }).click();
  await p.getByRole("heading", { name: "Mis eventos" }).waitFor({ timeout: 5000 });
  await p.getByText("Boda Valeria & Eduardo").waitFor();
  await p.getByText("XV años de Regina").waitFor();
  await p.getByText("Mariana Fuentes").waitFor();
  await p.screenshot({ path: `${SHOTS}06-eventos.png` });
});

await p.getByText("Boda Valeria & Eduardo").click();
await check("panel: 25 grupos, resumen suma el total", async () => {
  await p.getByText("25 de 25 grupos").waitFor({ timeout: 5000 });
  const n = await summaryNumbers(p);
  eq(n.conf + n.no + n.pend, n.total, "suma");
  ok(n.conf > 0 && n.no > 0 && n.pend > 0, "alguna categoría vacía");
});
await check("panel: categoría 'No asistirán', conteo por familias y parciales 'x de y'", async () => {
  const text = await p.locator("main").innerText();
  ok(text.includes("No asistirán"), "falta No asistirán");
  ok(/Por familias:\s*\d+ confirmaron · \d+ rechazaron · \d+ pendientes/.test(text.replace(/\n/g, " ")), "conteo familias");
  ok((await p.locator("tr", { hasText: "parcial" }).count()) >= 1, "sin parciales");
  ok(/Tíos Valenzuela[\s\S]*?\d de 3/.test(await p.locator("table").innerText()), "formato x de y");
});
await check("panel: barra con tres tramos y etiqueta accesible", async () => {
  const bar = p.getByRole("img", { name: /Confirmados: \d+ de \d+ lugares/ });
  eq(await bar.locator("div").count(), 3, "tramos");
});
await p.screenshot({ path: `${SHOTS}07-panel.png`, fullPage: false });

await check("panel: fecha sigue en hora de Tijuana con navegador en Nueva York", async () => {
  ok((await p.locator("main").innerText()).includes("5:00"), "la hora no es 5:00 p.m. de Tijuana");
});
await check("filtro por estado", async () => {
  await p.getByRole("button", { name: "Rechazados" }).click();
  const rows = await p.locator("tbody tr").count();
  ok(rows > 0 && rows < 25, `filas ${rows}`);
  eq(await p.locator("tbody tr", { hasText: "Pendiente" }).count(), 0, "pendientes visibles");
  await p.getByRole("button", { name: "Todos" }).click();
});
await check("búsqueda ignora acentos", async () => {
  await p.getByLabel("Buscar por nombre").fill("duarte felix");
  await p.getByText("1 de 25 grupos").waitFor({ timeout: 3000 });
  await p.getByLabel("Buscar por nombre").fill("");
});
await check("copiar link", async () => {
  const row = p.locator("tr", { hasText: "Familia Duarte Félix" });
  await row.getByRole("button", { name: "Copiar link" }).click();
  await row.getByRole("button", { name: "¡Copiado!" }).waitFor({ timeout: 2000 });
  eq(await p.evaluate(() => navigator.clipboard.readText()), `${BASE}/i/demo-boda-rechazado`, "portapapeles");
});
await check("WhatsApp: wa.me con +52 y link prellenado", async () => {
  const row = p.locator("tr", { hasText: "Familia Duarte Félix" });
  const href = await row.getByRole("link", { name: "Enviar por WhatsApp" }).getAttribute("href");
  ok(/^https:\/\/wa\.me\/52664555\d{4}\?text=/.test(href), href);
  ok(decodeURIComponent(href).includes(`${BASE}/i/demo-boda-rechazado`), "sin link");
  eq(await row.getByRole("link", { name: "Enviar por WhatsApp" }).getAttribute("target"), "_blank", "target");
});
await check("agregar invitado sin teléfono: WhatsApp desactivado", async () => {
  await p.getByRole("button", { name: "Agregar invitado" }).click();
  await p.getByLabel("Familia o grupo").fill("Familia Prueba E2E");
  await p.getByLabel("Lugares asignados").fill("4");
  await p.screenshot({ path: `${SHOTS}08-agregar.png` });
  await p.getByRole("button", { name: "Guardar" }).click();
  const row = p.locator("tr", { hasText: "Familia Prueba E2E" });
  await row.waitFor({ timeout: 5000 });
  ok(await row.getByRole("button", { name: "Enviar por WhatsApp" }).isDisabled(), "debería estar desactivado");
});
await check("editar: agregar teléfono activa WhatsApp", async () => {
  const row = p.locator("tr", { hasText: "Familia Prueba E2E" });
  await row.getByRole("button", { name: "Editar" }).click();
  await p.getByLabel("Teléfono").fill("664 555 0199");
  await p.getByRole("button", { name: "Guardar" }).click();
  await row.getByRole("link", { name: "Enviar por WhatsApp" }).waitFor({ timeout: 5000 });
});
await check("editar: no baja asignados por debajo de confirmados (mensaje del backend)", async () => {
  const row = p.locator("tr", { hasText: /[3-9] de [3-9](?![0-9])/ }).first();
  await row.getByRole("button", { name: "Editar" }).click();
  const dialog = p.getByRole("dialog");
  await dialog.getByText(/ya confirmó [0-9]+ lugares/).waitFor({ timeout: 3000 });
  const input = dialog.getByLabel(/Lugares asignados/);
  await input.evaluate((el) => el.removeAttribute("min"));
  await input.fill("1");
  await dialog.getByRole("button", { name: "Guardar" }).click();
  await dialog.getByRole("alert").waitFor({ timeout: 5000 });
  ok((await dialog.getByRole("alert").innerText()).includes("no puedes asignarle menos"), "mensaje");
  await p.screenshot({ path: `${SHOTS}09-editar-limite.png` });
  await dialog.getByRole("button", { name: "Cancelar" }).click();
});
await check("eliminar pendiente: pide confirmación sin advertencia extra", async () => {
  const row = p.locator("tr", { hasText: "Familia Prueba E2E" });
  await row.getByRole("button", { name: "Eliminar" }).click();
  const dialog = p.getByRole("dialog");
  await dialog.getByText("Su link dejará de funcionar").waitFor({ timeout: 3000 });
  eq(await dialog.getByText("Atención:").count(), 0, "advertencia");
  await dialog.getByRole("button", { name: "Eliminar" }).click();
  await row.waitFor({ state: "detached", timeout: 5000 });
});
await check("eliminar confirmado: advertencia extra y el link muere con mensaje amable", async () => {
  const row = p.locator("tr", { hasText: "Familia Ibarra Montes" });
  await row.getByRole("button", { name: "Eliminar" }).click();
  const dialog = p.getByRole("dialog");
  await dialog.getByText("Atención:").waitFor({ timeout: 3000 });
  await p.screenshot({ path: `${SHOTS}10-eliminar-confirmado.png` });
  await dialog.getByRole("button", { name: "Eliminar" }).click();
  await row.waitFor({ state: "detached", timeout: 5000 });
  await inv.goto(`${BASE}/i/demo-boda-confirmado`);
  await inv.getByRole("heading", { name: "Invitación no disponible" }).waitFor({ timeout: 5000 });
});
await check("importar CSV: válidas entran y errores se reportan por fila", async () => {
  await p.getByRole("button", { name: "Importar CSV" }).click();
  const dialog = p.getByRole("dialog");
  await dialog.getByLabel("Archivo CSV").setInputFiles({
    name: "invitados.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("nombre_grupo;telefono;lugares_asignados\nFamilia Peña Importada;6645550150;4\nFamilia Mala;6645550151;0\n", "utf-8"),
  });
  await dialog.getByRole("button", { name: "Importar" }).click();
  await dialog.getByText("1 invitado importado, 1 fila con error").waitFor({ timeout: 5000 });
  await dialog.getByText(/Fila 3:/).waitFor();
  await p.screenshot({ path: `${SHOTS}11-importar.png` });
  await dialog.getByRole("button", { name: "Cerrar" }).click();
  await p.locator("tr", { hasText: "Familia Peña Importada" }).waitFor({ timeout: 5000 });
});
await check("exportar Excel: descarga .xlsx válido", async () => {
  const [download] = await Promise.all([
    p.waitForEvent("download", { timeout: 8000 }),
    p.getByRole("button", { name: "Exportar a Excel" }).click(),
  ]);
  eq(download.suggestedFilename(), "invitados-boda-valeria-eduardo.xlsx", "nombre");
  const path = `${SHOTS}../export.xlsx`;
  await download.saveAs(path);
  eq(fs.readFileSync(path).subarray(0, 2).toString(), "PK", "firma zip");
});
await check("polling: el panel refleja un RSVP sin recargar (<= 16 s)", async () => {
  const before = await summaryNumbers(p);
  await inv.goto(`${BASE}/i/demo-boda-rechazado`);
  await inv.getByRole("button", { name: "Cambiar mi respuesta" }).click({ timeout: 5000 });
  await inv.getByText("Sí, asistiremos").click();
  await inv.getByRole("button", { name: "Enviar respuesta" }).click();
  await inv.getByRole("heading", { name: "¡Gracias!" }).waitFor({ timeout: 5000 });
  const start = Date.now();
  await p.waitForFunction(
    (conf) => {
      const text = document.querySelector('[aria-label="Resumen de confirmaciones"]').innerText;
      return Number(text.match(/Confirmados\s+(\d+)/)[1]) > conf;
    },
    before.conf,
    { timeout: 16500 },
  );
  console.log(`     (actualizó en ${((Date.now() - start) / 1000).toFixed(1)} s)`);
});
await check("editar evento: la fecha no se mueve al guardar", async () => {
  await p.getByRole("link", { name: "Editar evento" }).click();
  const field = p.getByLabel("Fecha y hora del evento");
  await field.waitFor({ timeout: 5000 });
  const before = await field.inputValue();
  ok(before.endsWith("T17:00"), `hora ${before}`);
  await p.getByRole("button", { name: "Guardar evento" }).click();
  await p.getByRole("link", { name: "Editar evento" }).click();
  await field.waitFor({ timeout: 5000 });
  eq(await field.inputValue(), before, "fecha");
  await p.getByRole("link", { name: "Cancelar" }).click();
});
await check("crear evento y validar límite posterior al evento", async () => {
  await p.getByRole("link", { name: "← Mis eventos" }).click();
  await p.getByRole("link", { name: "Nuevo evento" }).click();
  await p.getByLabel("Nombre del evento").fill("Cumpleaños de prueba");
  await p.getByLabel("Tipo").selectOption("cumpleaños");
  await p.getByLabel("Fecha y hora del evento").fill("2031-01-10T18:00");
  await p.getByLabel("Fecha límite para confirmar").fill("2031-02-10T18:00");
  await p.getByLabel("Nombre del lugar").fill("Salón Prueba");
  await p.getByRole("textbox", { name: "Dirección", exact: true }).fill("Zona Río, Tijuana");
  await p.screenshot({ path: `${SHOTS}12-form-evento.png`, fullPage: true });
  await p.getByRole("button", { name: "Guardar evento" }).click();
  await p.getByText("La fecha límite no puede ser posterior al evento").waitFor({ timeout: 5000 });
  await p.getByLabel("Fecha límite para confirmar").fill("2020-01-01T18:00");
  await p.getByRole("button", { name: "Guardar evento" }).click();
  await p.getByRole("heading", { name: "Cumpleaños de prueba" }).waitFor({ timeout: 5000 });
  await p.getByText("Aún no hay invitados").waitFor();
});
await check("tras la fecha límite la invitación es solo lectura", async () => {
  await p.getByRole("button", { name: "Agregar invitado" }).click();
  await p.getByLabel("Familia o grupo").fill("Familia Tardía");
  await p.getByRole("button", { name: "Guardar" }).click();
  const row = p.locator("tr", { hasText: "Familia Tardía" });
  await row.waitFor({ timeout: 5000 });
  await row.getByRole("button", { name: "Copiar link" }).click();
  await row.getByRole("button", { name: "¡Copiado!" }).waitFor({ timeout: 2000 });
  const link = await p.evaluate(() => navigator.clipboard.readText());
  await inv.goto(link);
  await inv.getByText("La fecha límite para confirmar ya pasó").waitFor({ timeout: 5000 });
  eq(await inv.getByRole("button", { name: "Enviar respuesta" }).count(), 0, "formulario");
  eq(await inv.getByText("Sí, asistiremos").count(), 0, "opciones");
  await inv.screenshot({ path: `${SHOTS}13-solo-lectura.png`, fullPage: true });
});
await check("panel en móvil: sin scroll horizontal de página", async () => {
  await p.setViewportSize({ width: 390, height: 844 });
  await p.getByRole("link", { name: "← Mis eventos" }).click();
  await p.getByText("XV años de Regina").click();
  await p.getByText("25 de 25 grupos").waitFor({ timeout: 5000 });
  ok(await noHScroll(p), "scroll horizontal");
  await p.screenshot({ path: `${SHOTS}14-panel-movil.png` });
  await p.setViewportSize({ width: 1280, height: 900 });
});
await check("salir cierra la sesión", async () => {
  await p.getByRole("button", { name: "Salir" }).click();
  await p.waitForURL("**/login", { timeout: 5000 });
  await p.goto(`${BASE}/`);
  await p.waitForURL("**/login", { timeout: 5000 });
});

await browser.close();

// Los 404 y 401 provocados a propósito se registran como error de red en consola.
const unexpected = consoleErrors.filter((line) => !/status of (401|404|409|422)/.test(line));
const failed = results.filter(([state]) => state === "FAIL").length;
console.log(`\n${results.length - failed}/${results.length} comprobaciones OK`);
console.log(`Errores de consola inesperados: ${unexpected.length}`);
unexpected.slice(0, 10).forEach((line) => console.log("  ", line));
process.exit(failed || unexpected.length ? 1 : 0);
