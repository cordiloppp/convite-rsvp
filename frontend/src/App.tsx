import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { api, getToken, setToken } from "./api/client";
import type { Planner } from "./api/types";
import { PlannerLayout } from "./components/PlannerLayout";
import { ConfigProvider, useConfig } from "./hooks/useConfig";
import EventoDetalle from "./pages/planner/EventoDetalle";
import EventoForm from "./pages/planner/EventoForm";
import Eventos from "./pages/planner/Eventos";
import Login from "./pages/planner/Login";
import Invitacion from "./pages/public/Invitacion";

function PlannerArea() {
  const location = useLocation();
  const navigate = useNavigate();
  const { brand_name } = useConfig();
  const [planner, setPlanner] = useState<Planner | null>(null);
  const token = getToken();

  useEffect(() => {
    document.title = brand_name;
  }, [brand_name]);

  useEffect(() => {
    if (!token) return;
    api
      .me()
      .then(setPlanner)
      .catch(() => {
        setToken(null);
        navigate("/login", { replace: true });
      });
  }, [token, navigate]);

  useEffect(() => {
    const onExpired = () => navigate("/login", { replace: true });
    window.addEventListener("convite:sesion-expirada", onExpired);
    return () => window.removeEventListener("convite:sesion-expirada", onExpired);
  }, [navigate]);

  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (!planner) return <p className="p-10 text-center text-sm text-gris">Cargando…</p>;
  return <PlannerLayout nombre={planner.nombre} />;
}

export default function App() {
  return (
    <ConfigProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/i/:token" element={<Invitacion />} />
          <Route path="/login" element={<Login />} />
          <Route element={<PlannerArea />}>
            <Route path="/" element={<Eventos />} />
            <Route path="/eventos/nuevo" element={<EventoForm />} />
            <Route path="/eventos/:id" element={<EventoDetalle />} />
            <Route path="/eventos/:id/editar" element={<EventoForm />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
