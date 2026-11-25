import { useState, type FormEvent } from "react";
import { api } from "../../api/client";
import type { Guest, ImportResult } from "../../api/types";
import { Button, Dialog, ErrorBanner, Field, inputClass } from "../../components/ui";
import { plural } from "../../lib/format";

export function GuestFormDialog({
  eventId,
  guest,
  onClose,
  onSaved,
}: {
  eventId: number;
  guest: Guest | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [nombre, setNombre] = useState(guest?.nombre_grupo ?? "");
  const [telefono, setTelefono] = useState(guest?.telefono ?? "");
  const [lugares, setLugares] = useState(String(guest?.lugares_asignados ?? 2));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const minimo = Math.max(1, guest?.lugares_confirmados ?? 1);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const data = {
      nombre_grupo: nombre,
      telefono: telefono.trim() || null,
      lugares_asignados: Number(lugares),
    };
    try {
      if (guest) await api.updateGuest(eventId, guest.id, data);
      else await api.createGuest(eventId, data);
      onSaved();
    } catch (reason) {
      setError((reason as Error).message);
      setSaving(false);
    }
  }

  return (
    <Dialog title={guest ? "Editar invitado" : "Agregar invitado"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {error && <ErrorBanner>{error}</ErrorBanner>}
        <Field label="Familia o grupo">
          <input
            className={inputClass}
            required
            maxLength={200}
            placeholder="Familia López"
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
          />
        </Field>
        <Field label="Teléfono" hint="10 dígitos. Sin teléfono no se puede enviar por WhatsApp.">
          <input
            className={inputClass}
            type="tel"
            placeholder="664 555 0101"
            value={telefono}
            onChange={(event) => setTelefono(event.target.value)}
          />
        </Field>
        <Field
          label="Lugares asignados"
          hint={
            minimo > 1
              ? `Esta familia ya confirmó ${minimo} lugares: no puedes asignarle menos.`
              : undefined
          }
        >
          <input
            className={inputClass}
            type="number"
            required
            min={minimo}
            max={100}
            value={lugares}
            onChange={(event) => setLugares(event.target.value)}
          />
        </Field>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? "Guardando…" : "Guardar"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

export function DeleteGuestDialog({
  eventId,
  guest,
  onClose,
  onDeleted,
}: {
  eventId: number;
  guest: Guest;
  onClose: () => void;
  onDeleted: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function confirm() {
    setDeleting(true);
    setError(null);
    try {
      await api.deleteGuest(eventId, guest.id);
      onDeleted();
    } catch (reason) {
      setError((reason as Error).message);
      setDeleting(false);
    }
  }

  return (
    <Dialog title="Eliminar invitado" onClose={onClose}>
      <div className="space-y-3 text-sm">
        {error && <ErrorBanner>{error}</ErrorBanner>}
        <p>
          ¿Eliminar a <strong>{guest.nombre_grupo}</strong>? Su link dejará de funcionar y esto no
          se puede deshacer.
        </p>
        {guest.estado === "confirmado" && (
          <p className="rounded-md border border-peligro/30 bg-peligro/5 px-3 py-2 text-peligro">
            <strong>Atención:</strong> esta familia ya confirmó{" "}
            {plural(guest.lugares_confirmados, "lugar", "lugares")}. Al eliminarla, esos lugares
            saldrán de tu resumen.
          </p>
        )}
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Cancelar
        </Button>
        <Button variant="danger" onClick={confirm} disabled={deleting}>
          {deleting ? "Eliminando…" : "Eliminar"}
        </Button>
      </div>
    </Dialog>
  );
}

export function ImportDialog({
  eventId,
  onClose,
  onImported,
}: {
  eventId: number;
  onClose: () => void;
  onImported: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setSending(true);
    setError(null);
    setResult(null);
    try {
      const imported = await api.importGuests(eventId, file);
      setResult(imported);
      if (imported.importados > 0) onImported();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setSending(false);
    }
  }

  return (
    <Dialog title="Importar desde CSV" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {error && <ErrorBanner>{error}</ErrorBanner>}
        <p className="text-sm text-gris">
          El archivo debe tener las columnas <code>nombre_grupo</code>, <code>telefono</code> y{" "}
          <code>lugares_asignados</code>.{" "}
          <a className="text-dorado underline" href="/ejemplo-invitados.csv" download>
            Descargar ejemplo
          </a>
        </p>
        <input
          className={inputClass}
          type="file"
          accept=".csv,text/csv"
          required
          aria-label="Archivo CSV"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />

        {result && (
          <div className="space-y-2 text-sm" role="status">
            <p className="font-medium">
              {plural(result.importados, "invitado importado", "invitados importados")}
              {result.errores.length > 0 &&
                `, ${plural(result.errores.length, "fila con error", "filas con error")}`}
            </p>
            {result.errores.length > 0 && (
              <ul className="max-h-40 space-y-1 overflow-y-auto rounded-md border border-linea bg-white p-3 text-gris">
                {result.errores.map((rowError) => (
                  <li key={rowError.fila}>
                    Fila {rowError.fila}: {rowError.mensaje}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose}>
            {result ? "Cerrar" : "Cancelar"}
          </Button>
          <Button type="submit" disabled={!file || sending}>
            {sending ? "Importando…" : "Importar"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
