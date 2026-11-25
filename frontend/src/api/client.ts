import type {
  EventData,
  EventInput,
  EventListItem,
  EventPanel,
  Guest,
  GuestInput,
  ImportResult,
  Invitation,
  Planner,
  PublicConfig,
  RsvpInput,
} from "./types";

const TOKEN_KEY = "convite.token";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Sin almacenamiento la sesión dura solo mientras la pestaña siga abierta.
  }
}

/** True unless the session token was issued without write access (public demo). */
export function canWrite(): boolean {
  const token = getToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))) as {
      rw?: boolean;
    };
    return payload.rw !== false;
  } catch {
    return false;
  }
}

async function send(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(path, { ...init, headers });
  } catch {
    throw new ApiError("No se pudo conectar. Revisa tu conexión e intenta de nuevo.", 0);
  }
  if (response.ok) return response;

  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  const detail = typeof body?.detail === "string" ? body.detail : "Ocurrió un error inesperado";
  if (response.status === 401 && token) {
    setToken(null);
    window.dispatchEvent(new Event("convite:sesion-expirada"));
  }
  throw new ApiError(detail, response.status);
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  return (await send(path, init)).json() as Promise<T>;
}

function jsonBody(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  config: () => json<PublicConfig>("/api/config"),
  login: (email: string, password: string) =>
    json<{ access_token: string }>("/api/auth/login", jsonBody("POST", { email, password })),
  me: () => json<Planner>("/api/auth/me"),

  events: () => json<EventListItem[]>("/api/events"),
  event: (id: number) => json<EventData>(`/api/events/${id}`),
  createEvent: (data: EventInput) => json<EventData>("/api/events", jsonBody("POST", data)),
  updateEvent: (id: number, data: EventInput) =>
    json<EventData>(`/api/events/${id}`, jsonBody("PUT", data)),
  panel: (id: number) => json<EventPanel>(`/api/events/${id}/panel`),

  createGuest: (eventId: number, data: GuestInput) =>
    json<Guest>(`/api/events/${eventId}/guests`, jsonBody("POST", data)),
  updateGuest: (eventId: number, guestId: number, data: GuestInput) =>
    json<Guest>(`/api/events/${eventId}/guests/${guestId}`, jsonBody("PUT", data)),
  deleteGuest: async (eventId: number, guestId: number) => {
    await send(`/api/events/${eventId}/guests/${guestId}`, { method: "DELETE" });
  },
  importGuests: (eventId: number, file: File) => {
    const body = new FormData();
    body.append("file", file);
    return json<ImportResult>(`/api/events/${eventId}/guests/import`, { method: "POST", body });
  },
  exportGuests: async (eventId: number) => {
    const response = await send(`/api/events/${eventId}/export`);
    const disposition = response.headers.get("Content-Disposition") ?? "";
    const match = disposition.match(/filename\*=UTF-8''(.+)$/);
    return {
      blob: await response.blob(),
      filename: match ? decodeURIComponent(match[1]) : "invitados.xlsx",
    };
  },

  invitation: (token: string) =>
    json<Invitation>(`/api/public/invitations/${encodeURIComponent(token)}`),
  rsvp: (token: string, data: RsvpInput) =>
    json<Invitation>(
      `/api/public/invitations/${encodeURIComponent(token)}/rsvp`,
      jsonBody("POST", data),
    ),
};
