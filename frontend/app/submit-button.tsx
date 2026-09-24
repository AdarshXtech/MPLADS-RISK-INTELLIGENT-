"use client";

import { useFormStatus } from "react-dom";
import { ArrowRight, LoaderCircle, Save } from "lucide-react";

export function SubmitButton({ children, pendingLabel, variant = "save" }: { children: React.ReactNode; pendingLabel: string; variant?: "save" | "login" }) {
  const { pending } = useFormStatus();
  const Icon = pending ? LoaderCircle : variant === "login" ? ArrowRight : Save;
  return <button type="submit" disabled={pending} aria-busy={pending}>
    <span>{pending ? pendingLabel : children}</span><Icon className={pending ? "spin" : undefined} size={17} aria-hidden="true" />
  </button>;
}
