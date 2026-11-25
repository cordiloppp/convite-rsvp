import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import type { EventInput, EventType } from "../../api/types";
import { Button, buttonClass, ErrorBanner, Field, inputClass } from "../../components/ui";
import { useConfig } from "../../hooks/useConfig";
import { EVENT_TYPES, toDateTimeInput } from "../../lib/format";

type FormState = {
  nombre: string;
  tipo: EventType;
  fecha_hora: string;
  lugar_nombre: string;
  direccion: string;
  link_mapa: string;
  mensaje: string;
  imagen_portada_url: string;
  fecha_limite_confirmacion: string;
};

const EMPTY: FormState = {
  nombre: "",
  tipo: "boda",
  fecha_hora: "",
  lugar_nombre: "",
  direccion: "",
  link_mapa: "",
  mensaje: "",
  imagen_portada_url: "",
  fecha_limite_confirmacion: "",
};

export default function EventoForm() {
  const { id } = useParams();
  const eventId = id ? Number(id) : null;
  const { timezone } = useConfig();
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(eventId !== null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (eventId === null) return;
    api
      .event(eventId)
      .then((event) =>
        setForm({
          nombre: event.nombre,
          tipo: event.tipo,
          fecha_hora: toDateTimeInput(event.fecha_hora),
          lugar_nombre: event.lugar_nombre,
          direccion: event.direccion,
          link_mapa: event.link_mapa ?? "",
          mensaje: event.mensaje ?? "",
          imagen_portada_url: event.imagen_portada_url ?? "",
          fecha_limite_confirmacion: toDateTimeInput(event.fecha_limite_confirmacion),
        }),
      )
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [eventId]);

  const set = (field: keyof FormState) => (value: string) =>
    setForm((current) => ({ ...current, [field]: value }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const data: EventInput = {
      ...form,
      link_mapa: form.link_mapa || null,
      mensaje: form.mensaje || null,
      imagen_portada_url: form.imagen_portada_url || null,
    };
    try {
      const saved = eventId
        ? await api.updateEvent(eventId, data)
        : await api.createEvent(data);
      navigate(`/eventos/${saved.id}`);
    } catch (reason) {
      setError((reason as Error).message);
      setSaving(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  const cancelTo = eventId ? `/eventos/${eventId}` : "/";

  if (loading) return <p className="text-sm text-gris">Cargando…</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 font-serif text-4xl font-medium">
        {eventId ? "Editar evento" : "Nuevo evento"}
      </h1>
      <form onSubmit={submit} className="space-y-5 rounded-lg border border-linea bg-white p-6">
        {error && <ErrorBanner>{error}</ErrorBanner>}

        <Field label="Nombre del evento">
          <input
            className={inputClass}
            required
            maxLength={200}
            placeholder="Boda Valeria & Eduardo"
            value={form.nombre}
            onChange={(event) => set("nombre")(event.target.value)}
          />
        </Field>

        <Field label="Tipo">
          <select
            className={inputClass}
            value={form.tipo}
            onChange={(event) => set("tipo")(event.target.value)}
          >
            {EVENT_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Fecha y hora del evento" hint={`Hora de ${timezone}`}>
            <input
              className={inputClass}
              type="datetime-local"
              required
              value={form.fecha_hora}
              onChange={(event) => set("fecha_hora")(event.target.value)}
            />
          </Field>
          <Field label="Fecha límite para confirmar" hint="Después, la invitación es solo lectura">
            <input
              className={inputClass}
              type="datetime-local"
              required
              value={form.fecha_limite_confirmacion}
              onChange={(event) => set("fecha_limite_confirmacion")(event.target.value)}
            />
          </Field>
        </div>

        <Field label="Nombre del lugar">
          <input
            className={inputClass}
            required
            maxLength={200}
            value={form.lugar_nombre}
            onChange={(event) => set("lugar_nombre")(event.target.value)}
          />
        </Field>

        <Field label="Dirección">
          <input
            className={inputClass}
            required
            maxLength={300}
            value={form.direccion}
            onChange={(event) => set("direccion")(event.target.value)}
          />
        </Field>

        <Field label="Link de Google Maps" hint="Si lo dejas vacío, se busca por la dirección">
          <input
            className={inputClass}
            type="url"
            value={form.link_mapa}
            onChange={(event) => set("link_mapa")(event.target.value)}
          />
        </Field>

        <Field label="Mensaje para los invitados">
          <textarea
            className={inputClass}
            rows={4}
            maxLength={2000}
            value={form.mensaje}
            onChange={(event) => set("mensaje")(event.target.value)}
          />
        </Field>

        <Field label="URL de la imagen de portada">
          <input
            className={inputClass}
            placeholder="https://…"
            value={form.imagen_portada_url}
            onChange={(event) => set("imagen_portada_url")(event.target.value)}
          />
        </Field>

        <div className="flex justify-end gap-2 pt-2">
          <Link to={cancelTo} className={buttonClass("ghost")}>
            Cancelar
          </Link>
          <Button type="submit" disabled={saving}>
            {saving ? "Guardando…" : "Guardar evento"}
          </Button>
        </div>
      </form>
    </div>
  );
}
