import { Link, Outlet, useNavigate } from "react-router-dom";
import { canWrite, setToken } from "../api/client";
import { useConfig } from "../hooks/useConfig";
import { DemoBanner } from "./DemoBanner";
import { Button } from "./ui";

export function PlannerLayout({ nombre }: { nombre: string }) {
  const { brand_name } = useConfig();
  const navigate = useNavigate();

  const demo = !canWrite();

  function logout() {
    setToken(null);
    // In the read-only demo, "Salir" leads to the owner's login instead of re-entering.
    navigate(demo ? "/login?cuenta" : "/login", { replace: true });
  }

  return (
    <div className="min-h-dvh">
      <header className="border-b border-linea bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="font-serif text-2xl font-medium tracking-wide">
            {brand_name}
          </Link>
          <div className="flex items-center gap-2">
            <span className="hidden text-sm text-gris sm:inline">{nombre}</span>
            <Button variant="ghost" onClick={logout}>
              {demo ? "Entrar con cuenta" : "Salir"}
            </Button>
          </div>
        </div>
      </header>
      <DemoBanner />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
