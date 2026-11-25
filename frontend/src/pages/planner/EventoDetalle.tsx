import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import type { Guest, GuestStatus } from "../../api/types";
import { ResumenPanel } from "../../components/ResumenBar";
import { Button, buttonClass, ErrorBanner, inputClass, StatusBadge } from "../../components/ui";
import { useConfig } from "../../hooks/useConfig";
import { usePolling } from "../../hooks/usePolling";
import {
  eventTypeLabel,
  formatDateShort,
  formatDateTimeShort,
  formatTime,
  normalizeText,
} from "../../lib/format";
import { DeleteGuestDialog, GuestFormDialog, ImportDialog } from "./GuestDialogs";

type StatusFilter = GuestStatus | "todos";
type OpenDialog =
  | { kind: "agregar" }
  | { kind: "importar" }
  | { kind: "editar"; guest: Guest }
  | { kind: "eliminar"; guest: Guest }
  | null;

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "todos", label: "Todos" },
  { value: "confirmado", label: "Confirmados" },
  { value: "rechazado", label: "Rechazados" },
  { value: "pendiente", label: "Pendientes" },
];

async function copyText(text: string): Promise<void> {
  // navigator.clipboard solo existe en HTTPS o localhost; por IP local hace falta el respaldo.
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const field = document.createElement("textarea");
  field.value = text;
  field.style.position = "fixed";
  field.style.opacity = "0";
  document.body.append(field);
  field.select();
  document.execCommand("copy");
  field.remove();
}

function Lugares({ guest }: { guest: Guest }) {
  if (guest.estado === "pendiente") {
    return <span className="text-gris">— de {guest.lugares_asignados}</span>;
  }
  const parcial =
    guest.estado === "confirmado" && guest.lugares_confirmados < guest.lugares_asignados;
  return (
    <span className={parcial ? "font-semibold text-dorado" : ""}>
      {guest.lugares_confirmados} de {guest.lugares_asignados}
      {parcial && <span className="ml-1.5 text-xs font-normal">parcial</span>}
    </span>
  );
}

function GuestRow({
  guest,
  timezone,
  onEdit,
  onDelete,
}: {
  guest: Guest;
  timezone: string;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await copyText(guest.link);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <tr className="border-t border-linea align-top">
      <td className="px-4 py-3">
        <p className="font-medium">{guest.nombre_grupo}</p>
        {guest.telefono && <p className="text-xs text-gris">{guest.telefono}</p>}
        {guest.nota && <p className="mt-1 max-w-xs text-xs text-gris italic">“{guest.nota}”</p>}
      </td>
      <td className="px-4 py-3">
        <StatusBadge estado={guest.estado} />
        {guest.confirmado_at && (
          <p className="mt-1 whitespace-nowrap text-xs text-gris">
            {formatDateTimeShort(guest.confirmado_at, timezone)}
          </p>
        )}
      </td>
      <td className="px-4 py-3 whitespace-nowrap tabular-nums">
        <Lugares guest={guest} />
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-wrap justify-end gap-1">
          <Button variant="secondary" className="!px-2.5 !py-1 text-xs" onClick={copy}>
            {copied ? "¡Copiado!" : "Copiar link"}
          </Button>
          {guest.whatsapp_url ? (
            <a
              className={buttonClass("secondary", "!px-2.5 !py-1 text-xs")}
              href={guest.whatsapp_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Enviar por WhatsApp
            </a>
          ) : (
            <Button
              variant="secondary"
              className="!px-2.5 !py-1 text-xs"
              disabled
              title="Agrega un teléfono válido para enviar por WhatsApp"
            >
              Enviar por WhatsApp
            </Button>
          )}
          <Button variant="ghost" className="!px-2.5 !py-1 text-xs" onClick={onEdit}>
            Editar
          </Button>
          <Button variant="ghost" className="!px-2.5 !py-1 text-xs" onClick={onDelete}>
            Eliminar
          </Button>
        </div>
      </td>
    </tr>
  );
}

export default function EventoDetalle() {
  const eventId = Number(useParams().id);
  const { timezone } = useConfig();
  const { data, error, updatedAt, refresh } = usePolling(() => api.panel(eventId), eventId);
  const [filter, setFilter] = useState<StatusFilter>("todos");
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<OpenDialog>(null);
  const [exporting, setExporting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const guests = useMemo(() => {
    const term = normalizeText(search.trim());
    return (data?.guests ?? []).filter(
      (guest) =>
        (filter === "todos" || guest.estado === filter) &&
        normalizeText(guest.nombre_grupo).includes(term),
    );
  }, [data, filter, search]);

  async function exportExcel() {
    setExporting(true);
    setActionError(null);
    try {
      const { blob, filename } = await api.exportGuests(eventId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setActionError((reason as Error).message);
    } finally {
      setExporting(false);
    }
  }

  const closeAndRefresh = () => {
    setDialog(null);
    void refresh();
  };

  if (!data) {
    if (error) {
      return (
        <div className="space-y-4">
          <ErrorBanner>{error.message}</ErrorBanner>
          <Link to="/" className={buttonClass("secondary")}>
            Volver a mis eventos
          </Link>
        </div>
      );
    }
    return <p className="text-sm text-gris">Cargando…</p>;
  }

  const { event, resumen } = data;

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-sm text-gris hover:text-tinta">
          ← Mis eventos
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium tracking-wider text-dorado uppercase">
              {eventTypeLabel(event.tipo)}
            </p>
            <h1 className="font-serif text-4xl font-medium">{event.nombre}</h1>
            <p className="mt-1 text-sm text-gris">
              {formatDateShort(event.fecha_hora, timezone)}, {formatTime(event.fecha_hora, timezone)}{" "}
              · {event.lugar_nombre}
            </p>
            <p className="text-sm text-gris">
              Confirman hasta el {formatDateShort(event.fecha_limite_confirmacion, timezone)}
            </p>
          </div>
          <Link to={`/eventos/${event.id}/editar`} className={buttonClass("secondary")}>
            Editar evento
          </Link>
        </div>
      </div>

      <ResumenPanel resumen={resumen} />

      {actionError && <ErrorBanner>{actionError}</ErrorBanner>}
      {error && (
        <ErrorBanner>No se pudo actualizar. Se muestra la última información recibida.</ErrorBanner>
      )}

      <section aria-label="Invitados" className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-serif text-2xl font-medium">Invitados</h2>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => setDialog({ kind: "agregar" })}>Agregar invitado</Button>
            <Button variant="secondary" onClick={() => setDialog({ kind: "importar" })}>
              Importar CSV
            </Button>
            <Button variant="secondary" onClick={exportExcel} disabled={exporting}>
              {exporting ? "Exportando…" : "Exportar a Excel"}
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            className={`${inputClass} !w-full sm:!w-72`}
            type="search"
            placeholder="Buscar por nombre"
            aria-label="Buscar por nombre"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <div className="flex flex-wrap gap-1" role="group" aria-label="Filtrar por estado">
            {FILTERS.map((option) => (
              <button
                key={option.value}
                type="button"
                aria-pressed={filter === option.value}
                onClick={() => setFilter(option.value)}
                className={`rounded-full px-3 py-1 text-sm transition-colors ${
                  filter === option.value
                    ? "bg-tinta text-marfil"
                    : "text-gris hover:bg-marfil-oscuro"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-linea bg-white">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="text-xs text-gris">
              <tr>
                <th scope="col" className="px-4 py-2.5 font-medium">Familia o grupo</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Estado</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Lugares</th>
                <th scope="col" className="px-4 py-2.5 text-right font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {guests.map((guest) => (
                <GuestRow
                  key={guest.id}
                  guest={guest}
                  timezone={timezone}
                  onEdit={() => setDialog({ kind: "editar", guest })}
                  onDelete={() => setDialog({ kind: "eliminar", guest })}
                />
              ))}
            </tbody>
          </table>
          {guests.length === 0 && (
            <p className="border-t border-linea p-8 text-center text-sm text-gris">
              {data.guests.length === 0
                ? "Aún no hay invitados. Agrégalos uno por uno o importa un CSV."
                : "Ningún invitado coincide con la búsqueda."}
            </p>
          )}
        </div>

        <p className="text-xs text-gris" aria-live="polite">
          {guests.length} de {data.guests.length} grupos
          {updatedAt && ` · Actualizado a las ${updatedAt.toLocaleTimeString("es-MX")}`}
        </p>
      </section>

      {(dialog?.kind === "agregar" || dialog?.kind === "editar") && (
        <GuestFormDialog
          eventId={event.id}
          guest={dialog.kind === "editar" ? dialog.guest : null}
          onClose={() => setDialog(null)}
          onSaved={closeAndRefresh}
        />
      )}
      {dialog?.kind === "eliminar" && (
        <DeleteGuestDialog
          eventId={event.id}
          guest={dialog.guest}
          onClose={() => setDialog(null)}
          onDeleted={closeAndRefresh}
        />
      )}
      {dialog?.kind === "importar" && (
        <ImportDialog
          eventId={event.id}
          onClose={() => setDialog(null)}
          onImported={() => void refresh()}
        />
      )}
    </div>
  );
}
