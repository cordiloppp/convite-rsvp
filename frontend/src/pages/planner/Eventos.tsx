import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { ResumenBar } from "../../components/ResumenBar";
import { buttonClass, ErrorBanner } from "../../components/ui";
import { useConfig } from "../../hooks/useConfig";
import { usePolling } from "../../hooks/usePolling";
import { eventTypeLabel, formatDateShort } from "../../lib/format";

export default function Eventos() {
  const { timezone } = useConfig();
  const { data: events, error } = usePolling(api.events, "eventos");

  return (
    <>
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="font-serif text-4xl font-medium">Mis eventos</h1>
        <Link to="/eventos/nuevo" className={buttonClass()}>
          Nuevo evento
        </Link>
      </div>

      {error && !events && <ErrorBanner>{error.message}</ErrorBanner>}
      {!events && !error && <p className="text-sm text-gris">Cargando…</p>}
      {events?.length === 0 && (
        <p className="rounded-lg border border-dashed border-linea p-10 text-center text-sm text-gris">
          Todavía no tienes eventos. Crea el primero para empezar a invitar.
        </p>
      )}

      <ul className="grid gap-4 md:grid-cols-2">
        {events?.map((event) => (
          <li key={event.id}>
            <Link
              to={`/eventos/${event.id}`}
              className="block rounded-lg border border-linea bg-white p-5 transition-colors hover:border-dorado-suave"
            >
              <p className="text-xs font-medium tracking-wider text-dorado uppercase">
                {eventTypeLabel(event.tipo)}
              </p>
              <h2 className="mt-1 font-serif text-2xl font-medium">{event.nombre}</h2>
              <p className="mt-1 text-sm text-gris">
                {formatDateShort(event.fecha_hora, timezone)} · {event.lugar_nombre}
              </p>
              <div className="mt-4">
                <ResumenBar resumen={event.resumen} compact />
              </div>
              <p className="mt-2 text-sm text-gris">
                <span className="font-medium text-tinta tabular-nums">
                  {event.resumen.lugares_confirmados}
                </span>{" "}
                de {event.resumen.lugares_total} lugares confirmados
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
