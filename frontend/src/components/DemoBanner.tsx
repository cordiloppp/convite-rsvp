import { canWrite } from "../api/client";
import { useConfig } from "../hooks/useConfig";

/** Shown on the public demo: visitors can look around, but changes are not saved. */
export function DemoBanner() {
  const { demo_readonly } = useConfig();
  if (!demo_readonly || canWrite()) return null;
  return (
    <div className="border-b border-dorado-suave/40 bg-dorado-suave/15 px-4 py-2 text-center text-sm text-dorado">
      Demo de solo lectura: puedes explorar todo, pero los cambios no se guardan.
    </div>
  );
}
