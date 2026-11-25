import type { Resumen } from "../api/types";
import { plural } from "../lib/format";

const SEGMENTS = [
  { key: "lugares_confirmados", label: "Confirmados", color: "bg-confirmado" },
  { key: "lugares_no_asistiran", label: "No asistirán", color: "bg-ausente" },
  { key: "lugares_pendientes", label: "Pendientes", color: "bg-linea" },
] as const;

export function ResumenBar({ resumen, compact = false }: { resumen: Resumen; compact?: boolean }) {
  const total = resumen.lugares_total;

  return (
    <div
      className={`flex w-full gap-0.5 overflow-hidden rounded ${compact ? "h-1.5" : "h-3"} ${
        total === 0 ? "bg-marfil-oscuro" : ""
      }`}
      role="img"
      aria-label={SEGMENTS.map(
        (segment) => `${segment.label}: ${resumen[segment.key]} de ${total} lugares`,
      ).join(", ")}
    >
      {SEGMENTS.map((segment) =>
        resumen[segment.key] > 0 ? (
          <div
            key={segment.key}
            className={segment.color}
            style={{ width: `${(resumen[segment.key] / total) * 100}%` }}
            title={`${segment.label}: ${resumen[segment.key]}`}
          />
        ) : null,
      )}
    </div>
  );
}

export function ResumenPanel({ resumen }: { resumen: Resumen }) {
  const total = resumen.lugares_total;
  const percent = (value: number) => (total ? `${Math.round((value / total) * 100)}%` : "0%");

  return (
    <section aria-label="Resumen de confirmaciones" className="rounded-lg border border-linea bg-white p-5">
      <div className="grid grid-cols-2 gap-x-4 gap-y-5 lg:grid-cols-4">
        <div>
          <p className="text-sm text-gris">Lugares asignados</p>
          <p className="font-serif text-4xl font-medium tabular-nums">{total}</p>
        </div>
        {SEGMENTS.map((segment) => (
          <div key={segment.key}>
            <p className="flex items-center gap-2 text-sm text-gris">
              <span aria-hidden className={`size-2.5 rounded-sm ${segment.color}`} />
              {segment.label}
            </p>
            <p className="font-serif text-4xl font-medium tabular-nums">
              {resumen[segment.key]}{" "}
              <span className="ml-1 font-sans text-sm font-normal text-gris">
                {percent(resumen[segment.key])}
              </span>
            </p>
          </div>
        ))}
      </div>

      <div className="mt-5">
        <ResumenBar resumen={resumen} />
      </div>

      <p className="mt-4 text-sm text-gris">
        <span className="font-medium text-tinta">Por familias: </span>
        {plural(resumen.familias_confirmadas, "confirmó", "confirmaron")} ·{" "}
        {plural(resumen.familias_rechazadas, "rechazó", "rechazaron")} ·{" "}
        {plural(resumen.familias_pendientes, "pendiente", "pendientes")}
      </p>
    </section>
  );
}
