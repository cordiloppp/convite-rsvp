import { useEffect, useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { ApiError, api } from "../../api/client";
import type { Invitation } from "../../api/types";
import { Button, buttonClass, ErrorBanner, Field, inputClass } from "../../components/ui";
import { DemoBanner } from "../../components/DemoBanner";
import { useConfig } from "../../hooks/useConfig";
import { formatDate, formatDateTimeShort, formatTime, plural } from "../../lib/format";

const COUNTDOWN_UNITS = [
  { label: "días", ms: 86_400_000 },
  { label: "horas", ms: 3_600_000 },
  { label: "min", ms: 60_000 },
  { label: "seg", ms: 1_000 },
];

function Countdown({ target }: { target: string }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  let remaining = new Date(target).getTime() - now;
  if (remaining <= 0) {
    return <p className="font-serif text-2xl text-dorado">¡Llegó el gran día!</p>;
  }

  return (
    <div className="grid grid-cols-4 gap-2" role="timer" aria-label="Tiempo restante">
      {COUNTDOWN_UNITS.map((unit) => {
        const value = Math.floor(remaining / unit.ms);
        remaining -= value * unit.ms;
        return (
          <div key={unit.label} className="rounded-md bg-marfil-oscuro/70 py-3">
            <p className="font-serif text-3xl leading-none font-medium tabular-nums">{value}</p>
            <p className="mt-1 text-xs text-gris">{unit.label}</p>
          </div>
        );
      })}
    </div>
  );
}

function Footer({ nombre, url }: { nombre: string; url: string }) {
  return (
    <footer className="py-8 text-center text-xs text-gris">
      Invitación hecha por{" "}
      <a href={url} target="_blank" rel="noopener noreferrer" className="underline">
        {nombre}
      </a>
    </footer>
  );
}

function respuestaTexto(guest: Invitation["guest"]): string {
  if (guest.estado === "rechazado") return "Nos avisaron que no podrán asistir.";
  const { lugares_confirmados: confirmados, lugares_asignados: asignados } = guest;
  return confirmados === asignados
    ? `Confirmaron ${plural(confirmados, "lugar", "lugares")}.`
    : `Confirmaron ${confirmados} de ${asignados} lugares.`;
}

function RsvpForm({
  token,
  invitation,
  onSaved,
  onCancel,
}: {
  token: string;
  invitation: Invitation;
  onSaved: (updated: Invitation) => void;
  onCancel?: () => void;
}) {
  const { guest } = invitation;
  const [asistira, setAsistira] = useState<boolean | null>(
    guest.estado === "pendiente" ? null : guest.estado === "confirmado",
  );
  const [lugares, setLugares] = useState(
    guest.lugares_confirmados || guest.lugares_asignados,
  );
  const [nota, setNota] = useState(guest.nota ?? "");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (asistira === null) return;
    setSending(true);
    setError(null);
    try {
      onSaved(
        await api.rsvp(token, {
          asistira,
          lugares: asistira ? lugares : null,
          nota: nota.trim() || null,
        }),
      );
    } catch (reason) {
      setError((reason as Error).message);
      setSending(false);
    }
  }

  const choice = (value: boolean, label: string) => (
    <label
      className={`flex cursor-pointer items-center justify-center rounded-md border px-3 py-3 text-sm font-medium transition-colors has-focus-visible:ring-2 has-focus-visible:ring-dorado ${
        asistira === value
          ? "border-tinta bg-tinta text-marfil"
          : "border-linea bg-white hover:border-dorado-suave"
      }`}
    >
      <input
        type="radio"
        name="asistira"
        className="sr-only"
        checked={asistira === value}
        onChange={() => setAsistira(value)}
      />
      {label}
    </label>
  );

  return (
    <form onSubmit={submit} className="space-y-5 text-left">
      {error && <ErrorBanner>{error}</ErrorBanner>}
      <fieldset>
        <legend className="mb-2 text-sm font-medium">¿Podrán acompañarnos?</legend>
        <div className="grid grid-cols-2 gap-2">
          {choice(true, "Sí, asistiremos")}
          {choice(false, "No podremos ir")}
        </div>
      </fieldset>

      {asistira === true && guest.lugares_asignados > 1 && (
        <Field label="¿Cuántos lugares usarán?">
          <select
            className={`${inputClass} !py-3`}
            value={lugares}
            onChange={(event) => setLugares(Number(event.target.value))}
          >
            {Array.from({ length: guest.lugares_asignados }, (_, index) => index + 1).map(
              (option) => (
                <option key={option} value={option}>
                  {plural(option, "lugar", "lugares")}
                </option>
              ),
            )}
          </select>
        </Field>
      )}

      {asistira !== null && (
        <Field label="Nota (opcional)">
          <textarea
            className={inputClass}
            rows={3}
            maxLength={500}
            placeholder="Alergias, felicitaciones o lo que quieran compartir"
            value={nota}
            onChange={(event) => setNota(event.target.value)}
          />
        </Field>
      )}

      <div className="space-y-2">
        <Button type="submit" className="w-full !py-3" disabled={asistira === null || sending}>
          {sending ? "Enviando…" : "Enviar respuesta"}
        </Button>
        {onCancel && (
          <Button variant="ghost" className="w-full" onClick={onCancel}>
            Cancelar
          </Button>
        )}
      </div>
    </form>
  );
}

export default function Invitacion() {
  const { token = "" } = useParams();
  const config = useConfig();
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [failure, setFailure] = useState<"no-disponible" | "conexion" | null>(null);
  const [editing, setEditing] = useState(false);
  const [justSaved, setJustSaved] = useState(false);

  useEffect(() => {
    api
      .invitation(token)
      .then((result) => {
        setInvitation(result);
        document.title = result.event.nombre;
      })
      .catch((reason) =>
        setFailure(reason instanceof ApiError && reason.status === 404 ? "no-disponible" : "conexion"),
      );
  }, [token]);

  if (failure) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center px-4 text-center">
        <div className="max-w-sm">
          <h1 className="font-serif text-4xl font-medium">
            {failure === "no-disponible" ? "Invitación no disponible" : "No pudimos abrir tu invitación"}
          </h1>
          <p className="mt-3 text-gris">
            {failure === "no-disponible"
              ? "Este link ya no está activo. Si crees que es un error, contacta a quien te envió la invitación. ¡Gracias por tu comprensión!"
              : "Revisa tu conexión e intenta de nuevo en un momento."}
          </p>
        </div>
        <Footer nombre={config.brand_name} url={config.brand_url} />
      </main>
    );
  }

  if (!invitation) {
    return <p className="p-10 text-center text-sm text-gris">Abriendo tu invitación…</p>;
  }

  const { event, guest, puede_responder: abierta, timezone, marca } = invitation;
  const respondio = guest.estado !== "pendiente";
  const mostrarFormulario = abierta && (!respondio || editing);

  function onSaved(updated: Invitation) {
    setInvitation(updated);
    setEditing(false);
    setJustSaved(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (justSaved) {
    const asistira = guest.estado === "confirmado";
    return (
      <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center px-4 text-center">
        <div className="py-10">
          <p className="text-sm font-medium tracking-widest text-dorado uppercase">
            Respuesta recibida
          </p>
          <h1 className="mt-3 font-serif text-5xl font-medium">
            {asistira ? "¡Gracias!" : "Gracias por avisarnos"}
          </h1>
          <p className="mt-4 text-gris">
            {asistira
              ? `Los esperamos en ${event.nombre}. ${respuestaTexto(guest)}`
              : `Lamentamos que no puedan acompañarnos en ${event.nombre}.`}
          </p>
          <div className="mt-8 space-y-2">
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => {
                setJustSaved(false);
                setEditing(false);
              }}
            >
              Ver mi invitación
            </Button>
            <p className="text-xs text-gris">
              Pueden cambiar su respuesta hasta el{" "}
              {formatDateTimeShort(event.fecha_limite_confirmacion, timezone)}
            </p>
          </div>
        </div>
        <Footer nombre={marca.nombre} url={marca.url} />
      </main>
    );
  }

  return (
    <div className="mx-auto min-h-dvh max-w-md bg-white shadow-sm sm:my-6 sm:min-h-0 sm:rounded-lg sm:overflow-hidden">
      <DemoBanner />
      {event.imagen_portada_url && (
        <img
          src={event.imagen_portada_url}
          alt=""
          className="aspect-[8/5] w-full bg-marfil-oscuro object-cover"
        />
      )}

      <main className="space-y-8 px-6 py-8 text-center">
        <header>
          <h1 className="font-serif text-4xl leading-tight font-medium">{event.nombre}</h1>
          <p className="mt-3 text-gris first-letter:uppercase">
            {formatDate(event.fecha_hora, timezone)}
          </p>
          <p className="text-gris">{formatTime(event.fecha_hora, timezone)}</p>
        </header>

        <Countdown target={event.fecha_hora} />

        {event.mensaje && (
          <p className="font-serif text-xl leading-snug whitespace-pre-line">{event.mensaje}</p>
        )}

        <section aria-label="Lugar">
          <h2 className="font-serif text-2xl font-medium">{event.lugar_nombre}</h2>
          <p className="mt-1 text-sm text-gris">{event.direccion}</p>
          <a
            href={event.link_mapa}
            target="_blank"
            rel="noopener noreferrer"
            className={buttonClass("secondary", "mt-3")}
          >
            Ver en Google Maps
          </a>
        </section>

        <hr className="mx-auto w-16 border-dorado-suave" />

        <section aria-label="Confirmación de asistencia" className="space-y-4">
          <p className="font-serif text-2xl leading-snug">
            Hola {guest.nombre_grupo}, tienen{" "}
            {plural(
              guest.lugares_asignados,
              "lugar reservado",
              "lugares reservados",
            )}
          </p>

          {respondio && !mostrarFormulario && (
            <div className="rounded-md bg-marfil p-4">
              <p className="text-sm font-medium">{respuestaTexto(guest)}</p>
              {guest.nota && <p className="mt-1 text-sm text-gris italic">“{guest.nota}”</p>}
            </div>
          )}

          {mostrarFormulario && (
            <>
              <p className="text-sm text-gris">
                Confirmen antes del{" "}
                {formatDateTimeShort(event.fecha_limite_confirmacion, timezone)}
              </p>
              <RsvpForm
                token={token}
                invitation={invitation}
                onSaved={onSaved}
                onCancel={editing ? () => setEditing(false) : undefined}
              />
            </>
          )}

          {abierta && respondio && !editing && (
            <Button variant="secondary" className="w-full" onClick={() => setEditing(true)}>
              Cambiar mi respuesta
            </Button>
          )}

          {!abierta && (
            <p className="text-sm text-gris">
              {respondio
                ? "La fecha límite ya pasó, por lo que esta respuesta ya no se puede cambiar."
                : "La fecha límite para confirmar ya pasó. Si necesitan ayuda, contacten a los anfitriones."}
            </p>
          )}
        </section>

        <Footer nombre={marca.nombre} url={marca.url} />
      </main>
    </div>
  );
}
