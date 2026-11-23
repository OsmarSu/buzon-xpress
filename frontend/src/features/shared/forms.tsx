import { cloneElement, isValidElement, useId, useLayoutEffect, useRef, useState, type FormEvent, type ReactNode } from "react";

import { describeError, mutationSeries } from "../../services/api";
import { sizeLabel, sizeMeasurementNote, sizes } from "../../services/custody";
import { scheduleText } from "./hours";

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

function FieldHelp({ id, label, hint, example }: {
  id: string; label: string; hint?: string; example?: string;
}) {
  const [open, setOpen] = useState(false);
  const [above, setAbove] = useState(false);
  const root = useRef<HTMLSpanElement>(null);
  const tooltip = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    if (!open) return;
    const measure = () => {
      const row = root.current?.parentElement?.getBoundingClientRect();
      const height = tooltip.current?.offsetHeight ?? 0;
      if (row) setAbove(row.bottom + height + 12 > innerHeight && row.top > height + 96);
    };
    const closeOutside = (event: PointerEvent) => {
      if (event.target instanceof Node && !root.current?.contains(event.target)) setOpen(false);
    };
    measure();
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    document.addEventListener("pointerdown", closeOutside);
    return () => {
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
      document.removeEventListener("pointerdown", closeOutside);
    };
  }, [open]);

  return <span className="field-help" ref={root}
    onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}
    onKeyDown={(event) => {
      if (event.key === "Escape" && open) {
        event.preventDefault();
        event.stopPropagation();
        setOpen(false);
      }
    }}>
    <button type="button" className="field-help-trigger" aria-label={"Ayuda para " + label}
      aria-describedby={id} onClick={() => setOpen(true)}
      onFocus={(event) => { if (event.currentTarget.matches(":focus-visible")) setOpen(true); }}
      onBlur={() => setOpen(false)}>
      <span aria-hidden="true">?</span>
    </button>
    <span className="field-tooltip" role="tooltip" id={id} ref={tooltip} hidden={!open} data-above={above}>
      {hint && <span>{hint}</span>}
      {example && <span><strong>Ejemplo:</strong> {example}</span>}
    </span>
  </span>;
}

export function RequiredMark() {
  return <span className="required-mark" aria-hidden="true" title="Obligatorio"> *</span>;
}

export function Field({ label, children, hint, example, required }: {
  label: string; children: ReactNode; hint?: string; example?: string; required?: boolean;
}) {
  const id = useId();
  const helpId = id + "-help";
  const control = isValidElement<{ id?: string; required?: boolean; "aria-describedby"?: string }>(children)
    && typeof children.type === "string" && ["input", "select", "textarea"].includes(children.type)
    ? children : null;
  const controlId = control?.props.id ?? id;
  const mandatory = required ?? control?.props.required;
  const caption = <>{label}{mandatory && <RequiredMark />}</>;
  const descriptions = [control?.props["aria-describedby"], hint || example ? helpId : undefined]
    .filter(Boolean).join(" ");
  const help = (hint || example) && <FieldHelp id={helpId} label={label} hint={hint} example={example} />;

  return <div className="field">
    {control ? <>
      <div className="field-label-row">
        <label htmlFor={controlId}>{caption}</label>
        {help}
      </div>
      {cloneElement(control, { id: controlId, required: mandatory, "aria-describedby": descriptions || undefined })}
    </> : <>
      <label className="field-control"><span>{caption}</span>{children}</label>
      {help && <div className="field-label-row">{help}</div>}
    </>}
  </div>;
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
  return sizes.map((size) => <option key={size} value={size}>{sizeLabel[size].replace(" · hasta ", " · ").replaceAll(" × ", "×")}</option>);
}

export function SizeGuide() { return <p className="size-measurement-note">{sizeMeasurementNote}</p>; }

export function Hours({ name = "hours" }: { name?: string }) {
  return <input name={name} type="number" min={1} step={1} required />;
}

export function Amount() {
  return <input name="amount" inputMode="decimal" placeholder="0.00" pattern="[0-9]+\.[0-9]{2}" required />;
}

export function PaymentFields() {
  const [method, setMethod] = useState("EFECTIVO");
  const manual = method === "REFERENCIA_MANUAL";
  return <>
    <Field label="Medio de cobro" hint="Registra cómo se realizó el cobro en el punto." example="Selecciona Efectivo si recibiste dinero en mano. Referencia manual permite registrar el comprobante de un cobro realizado por otro medio.">
      <select name="payment_method" required value={method} onChange={(event) => setMethod(event.target.value)}>
        <option value="EFECTIVO">Efectivo</option>
        <option value="REFERENCIA_MANUAL">Referencia manual</option>
      </select>
    </Field>
    <Field label={manual ? "Referencia del cobro" : "Referencia del cobro (opcional)"} hint="Es obligatoria para el medio Referencia manual." example="Copia el número del comprobante recibido, por ejemplo REC-2026-015.">
      <input name="payment_reference" required={manual} maxLength={120} placeholder="Número de comprobante" />
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
    <div key={day}><dt>{day}</dt><dd>{scheduleText(schedule)}</dd></div>,
  )}</dl> : <p>El punto aún no ha publicado sus horarios.</p>;
}
