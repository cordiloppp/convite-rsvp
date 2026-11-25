import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { api, getToken, setToken } from "../../api/client";
import { Button, ErrorBanner, Field, inputClass } from "../../components/ui";
import { useConfig } from "../../hooks/useConfig";

export default function Login() {
  const { brand_name, demo_readonly } = useConfig();
  const navigate = useNavigate();
  const location = useLocation();
  // Public demo: visitors enter without an account. "?cuenta" shows the form (owner).
  const conCuenta = new URLSearchParams(location.search).has("cuenta");
  const destino = (location.state as { from?: string } | null)?.from ?? "/";
  const [demoFallo, setDemoFallo] = useState(false);

  useEffect(() => {
    if (!demo_readonly || conCuenta || getToken()) return;
    api
      .demoLogin()
      .then(({ access_token }) => {
        setToken(access_token);
        navigate(destino, { replace: true });
      })
      .catch(() => setDemoFallo(true));
  }, [demo_readonly, conCuenta, destino, navigate]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  if (getToken()) return <Navigate to="/" replace />;

  if (demo_readonly && !conCuenta && !demoFallo) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center gap-3 px-4 text-center">
        <p className="font-serif text-4xl font-medium tracking-wide">{brand_name}</p>
        <p className="text-sm text-gris">Abriendo la demo, no necesitas cuenta…</p>
        <Link to="/login?cuenta" className="text-xs text-gris underline underline-offset-4">
          Entrar con cuenta
        </Link>
      </main>
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSending(true);
    setError(null);
    try {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from ?? "/", { replace: true });
    } catch (reason) {
      setError((reason as Error).message);
      setSending(false);
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <h1 className="text-center font-serif text-5xl font-medium tracking-wide">{brand_name}</h1>
        <p className="mt-2 mb-8 text-center text-sm text-gris">Panel para planners de eventos</p>
        <form onSubmit={submit} className="space-y-4 rounded-lg border border-linea bg-white p-6">
          {error && <ErrorBanner>{error}</ErrorBanner>}
          <Field label="Email">
            <input
              className={inputClass}
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Field>
          <Field label="Contraseña">
            <input
              className={inputClass}
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>
          <Button type="submit" className="w-full" disabled={sending}>
            {sending ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </div>
    </main>
  );
}
