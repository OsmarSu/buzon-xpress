import { cloneElement, isValidElement, useId, useRef, useState, type FormEvent, type ReactNode } from "react";

import { describeError, mutationSeries } from "../../services/api";
import { sizeLabel, sizes } from "../../services/custody";

export function useTask() {
  const active = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(action: () => Promise<void>) {
    if (active.current) return;
    active.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      active.current = false;
      setBusy(false);
    }
  }

  return { busy, error, run, setError };
}

export function useMutation() {
  const [send] = useState(mutationSeries);
  return send;
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  const id = useId();
  if (isValidElement<{ id?: string }>(children) && children.type === "select") {
    const controlId = children.props.id ?? id;
    return <div className="field">
      <label htmlFor={controlId}>{label}</label>
      {cloneElement(children, { id: controlId })}
    </div>;
  }
  return <label className="field"><span>{label}</span>{children}</label>;
}

export function Status({ busy, error, message }: { busy?: boolean; error?: string; message?: string }) {
  return <>
    <p role="status" className="status">{busy ? "Procesando la solicitud…" : message}</p>
    {error && <p role="alert" className="error">{error}</p>}
  </>;
}

export function formData(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();
  return new FormData(event.currentTarget);
}

export function value(data: FormData, field: string) {
  return String(data.get(field) ?? "").trim();
}

export function SizeOptions() {
  return sizes.map((size) => <option key={size} value={size}>{sizeLabel[size]}</option>);
}

export function Hours({ name = "hours" }: { name?: string }) {
  return <input name={name} type="number" min={1} step={1} required />;
}

export function Amount() {
  return <input name="amount" inputMode="decimal" placeholder="0.00" pattern="[0-9]+\.[0-9]{2}" required />;
}

export function PaymentFields() {
  return <>
    <Field label="Medio de cobro">
      <select name="payment_method">
        <option value="EFECTIVO">Efectivo</option>
        <option value="REFERENCIA_MANUAL">Referencia manual</option>
      </select>
    </Field>
    <Field label="Referencia del cobro (si corresponde)">
      <input name="payment_reference" maxLength={120} />
    </Field>
  </>;
}

export function payment(data: FormData) {
  const reference = value(data, "payment_reference");
  return {
    payment_method: value(data, "payment_method"),
    ...(reference ? { payment_reference: reference } : {}),
  };
}

export function Schedule({ hours }: { hours: Record<string, unknown> }) {
  const entries = Object.entries(hours);
  return entries.length ? <dl className="details">{entries.map(([day, schedule]) =>
    <div key={day}><dt>{day}</dt><dd>{typeof schedule === "string" ? schedule : JSON.stringify(schedule)}</dd></div>,
  )}</dl> : <p>El punto aún no ha publicado sus horarios.</p>;
}
