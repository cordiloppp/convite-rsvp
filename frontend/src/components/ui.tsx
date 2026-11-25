import { useEffect, useRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import type { GuestStatus } from "../api/types";
import { STATUS_LABELS } from "../lib/format";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-tinta text-marfil hover:bg-[#35312b]",
  secondary: "border border-linea bg-white text-tinta hover:bg-marfil-oscuro",
  ghost: "text-gris hover:bg-marfil-oscuro hover:text-tinta",
  danger: "bg-peligro text-white hover:brightness-110",
};

export function buttonClass(variant: Variant = "primary", extra = ""): string {
  return (
    "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium " +
    `transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${extra}`
  );
}

export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type={type} className={buttonClass(variant, className)} {...props} />;
}

export const inputClass =
  "w-full rounded-md border border-linea bg-white px-3 py-2 text-sm text-tinta " +
  "placeholder:text-gris/70 focus:border-dorado focus:outline-none focus:ring-1 focus:ring-dorado";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium">{label}</span>
      {children}
      {hint && <span className="block text-xs text-gris">{hint}</span>}
    </label>
  );
}

export function ErrorBanner({ children }: { children: ReactNode }) {
  return (
    <p role="alert" className="rounded-md border border-peligro/30 bg-peligro/5 px-3 py-2 text-sm text-peligro">
      {children}
    </p>
  );
}

const BADGE_STYLES: Record<GuestStatus, string> = {
  confirmado: "bg-confirmado/12 text-[#6f5212]",
  rechazado: "bg-ausente/12 text-[#2f5288]",
  pendiente: "bg-marfil-oscuro text-gris",
};

export function StatusBadge({ estado }: { estado: GuestStatus }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE_STYLES[estado]}`}>
      {STATUS_LABELS[estado]}
    </span>
  );
}

export function Dialog({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-lg bg-marfil p-6 text-tinta shadow-xl backdrop:bg-tinta/50"
    >
      <h2 className="mb-4 font-serif text-2xl font-medium">{title}</h2>
      {children}
    </dialog>
  );
}
