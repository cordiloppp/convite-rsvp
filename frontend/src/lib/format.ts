import type { EventType, GuestStatus } from "../api/types";

export const EVENT_TYPES: { value: EventType; label: string }[] = [
  { value: "boda", label: "Boda" },
  { value: "xv", label: "XV años" },
  { value: "cumpleaños", label: "Cumpleaños" },
  { value: "otro", label: "Otro" },
];

export const eventTypeLabel = (tipo: EventType) =>
  EVENT_TYPES.find((option) => option.value === tipo)?.label ?? tipo;

export const STATUS_LABELS: Record<GuestStatus, string> = {
  pendiente: "Pendiente",
  confirmado: "Confirmado",
  rechazado: "Rechazado",
};

export function formatDate(iso: string, timeZone: string): string {
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "full", timeZone }).format(new Date(iso));
}

export function formatTime(iso: string, timeZone: string): string {
  return new Intl.DateTimeFormat("es-MX", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone,
  }).format(new Date(iso));
}

export function formatDateShort(iso: string, timeZone: string): string {
  return new Intl.DateTimeFormat("es-MX", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone,
  }).format(new Date(iso));
}

export function formatDateTimeShort(iso: string, timeZone: string): string {
  return `${formatDateShort(iso, timeZone)}, ${formatTime(iso, timeZone)}`;
}

export const plural = (count: number, singular: string, pluralForm: string) =>
  `${count} ${count === 1 ? singular : pluralForm}`;

// La API entrega las fechas con la hora local del evento: los primeros 16
// caracteres son justo el valor que espera <input type="datetime-local">.
export const toDateTimeInput = (iso: string | undefined) => iso?.slice(0, 16) ?? "";

export function normalizeText(text: string): string {
  return text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}
