import { Link, Outlet, useNavigate } from "react-router-dom";
import { setToken } from "../api/client";
import { useConfig } from "../hooks/useConfig";
import { DemoBanner } from "./DemoBanner";
import { Button } from "./ui";

export function PlannerLayout({ nombre }: { nombre: string }) {
  const { brand_name } = useConfig();
  const navigate = useNavigate();

  function logout() {
    setToken(null);
    navigate("/login", { replace: true });
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
              Salir
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
