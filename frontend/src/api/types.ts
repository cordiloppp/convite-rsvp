export type EventType = "boda" | "xv" | "cumpleaños" | "otro";
export type GuestStatus = "pendiente" | "confirmado" | "rechazado";

export type PublicConfig = {
  brand_name: string;
  brand_url: string;
  timezone: string;
  demo_readonly?: boolean;
};
export type Planner = { id: number; nombre: string; email: string };

export type EventData = {
  id: number;
  nombre: string;
  tipo: EventType;
  fecha_hora: string;
  lugar_nombre: string;
  direccion: string;
  link_mapa: string | null;
  mensaje: string | null;
  imagen_portada_url: string | null;
  fecha_limite_confirmacion: string;
  created_at: string;
};

export type EventInput = Omit<EventData, "id" | "created_at">;

export type Resumen = {
  lugares_total: number;
  lugares_confirmados: number;
  lugares_no_asistiran: number;
  lugares_pendientes: number;
  familias_total: number;
  familias_confirmadas: number;
  familias_rechazadas: number;
  familias_pendientes: number;
};

export type EventListItem = EventData & { resumen: Resumen };

export type Guest = {
  id: number;
  nombre_grupo: string;
  telefono: string | null;
  lugares_asignados: number;
  token: string;
  estado: GuestStatus;
  lugares_confirmados: number;
  nota: string | null;
  confirmado_at: string | null;
  link: string;
  whatsapp_url: string | null;
};

export type GuestInput = {
  nombre_grupo: string;
  telefono: string | null;
  lugares_asignados: number;
};

export type EventPanel = { event: EventData; resumen: Resumen; guests: Guest[] };

export type ImportResult = {
  importados: number;
  errores: { fila: number; mensaje: string }[];
};

export type Invitation = {
  event: Omit<EventData, "id" | "created_at" | "link_mapa"> & { link_mapa: string };
  guest: {
    nombre_grupo: string;
    lugares_asignados: number;
    estado: GuestStatus;
    lugares_confirmados: number;
    nota: string | null;
  };
  puede_responder: boolean;
  timezone: string;
  marca: { nombre: string; url: string };
};

export type RsvpInput = { asistira: boolean; lugares: number | null; nota: string | null };
