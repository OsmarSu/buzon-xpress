import { useEffect, useRef, useState } from "react";

import { custodyApi, type Point, type Quote, type Size } from "../../services/custody";
import { Field, formData, Schedule, SizeOptions, Status, useTask, value } from "../shared/forms";

const trackingLabels = {
  PENDIENTE: "Pendiente de recepción",
  RECIBIDA: "En custodia",
  FINALIZADA: "Finalizada",
};

export function PublicService({ initialReference, trackingOnly = false }: {
  initialReference: string | null;
  trackingOnly?: boolean;
}) {
  const [points, setPoints] = useState<Point[]>([]);
  const [result, setResult] = useState<Awaited<ReturnType<typeof custodyApi.tracking>>>();
  const [quote, setQuote] = useState<Quote>();
  const trackingHeading = useRef<HTMLHeadingElement>(null);
  const pointsTask = useTask();
  const tracking = useTask();
  const quoteTask = useTask();

  function loadPoints() {
    void pointsTask.run(async () => setPoints(await custodyApi.points()));
  }

  useEffect(() => {
    if (!trackingOnly) loadPoints();
  }, [trackingOnly]);

  useEffect(() => {
    if (initialReference) trackingHeading.current?.focus();
  }, [initialReference]);

  const trackingSection = <section id="seguimiento" className="public-tracking" aria-labelledby="tracking-heading">
    <div className="public-section-intro">
      <p className="public-eyebrow">Consulta pública</p>
      <h2 id="tracking-heading" ref={trackingHeading} tabIndex={-1}>Seguimiento del objeto</h2>
      <p>Con la referencia compartida puedes consultar el estado general, el punto y su horario.</p>
    </div>
    <div className="public-tracking-panel">
      <form aria-busy={tracking.busy} onSubmit={(event) => {
        const reference = value(formData(event), "reference");
        setResult(undefined);
        void tracking.run(async () => setResult(await custodyApi.tracking(reference)));
      }}>
        <Field label="Referencia pública">
          <input name="reference" defaultValue={initialReference ?? ""} autoComplete="off"
            spellCheck={false} required maxLength={180} />
        </Field>
        <button type="submit" disabled={tracking.busy}>Consultar estado</button>
      </form>
      <Status {...tracking} />
      {result && <div className="receipt public-tracking-result" aria-live="polite">
        <strong>{trackingLabels[result.state]}</strong>
        <p>{result.point_name}</p>
        <Schedule hours={result.opening_hours} />
      </div>}
    </div>
  </section>;

  if (trackingOnly) return trackingSection;

  return <div className="public-services">
    <section id="puntos" className="public-points" aria-labelledby="points-heading">
      <div className="public-section-intro">
        <p className="public-eyebrow">Planifica tu visita</p>
        <h2 id="points-heading">Puntos y horarios</h2>
        <p>Consulta dónde puedes dejar un objeto y calcula cuánto cuesta el plazo que necesitas.</p>
      </div>
      <div className="public-service-grid">
        <div className="public-point-list">
          <Status {...pointsTask} />
          {points.length > 0 ? <ul className="public-point-items">
            {points.map((point) => <li key={point.id}>
              <span className="public-point-pin" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" strokeWidth="1.7">
                  <path d="M19 10c0 5-7 11-7 11s-7-6-7-11a7 7 0 1 1 14 0Z" />
                  <circle cx="12" cy="10" r="2.4" />
                </svg>
              </span>
              <div>
                <h3>{point.name}</h3>
                <p>{point.address}</p>
                <Schedule hours={point.opening_hours} />
              </div>
            </li>)}
          </ul> : !pointsTask.busy && !pointsTask.error && <p>Actualmente no hay puntos activos.</p>}
          {pointsTask.error && <button type="button" className="secondary" onClick={loadPoints}>Volver a consultar</button>}
        </div>
        <div className="public-quote">
          <h3>Cotizar custodia</h3>
          <p>El costo depende del tamaño y del plazo. El operador confirma el importe al recibir el objeto.</p>
          {points.length > 0 && <form aria-busy={quoteTask.busy} onChange={() => {
            setQuote(undefined);
            quoteTask.setError("");
          }} onSubmit={(event) => {
            const data = formData(event);
            const point = value(data, "point");
            const size = value(data, "size") as Size;
            const hours = Number(value(data, "hours"));
            setQuote(undefined);
            void quoteTask.run(async () => setQuote(await custodyApi.quote(point, size, hours)));
          }}>
            <div className="field">
              <label htmlFor="public-quote-point">Punto de servicio</label>
              <select id="public-quote-point" name="point" required disabled={quoteTask.busy}
                defaultValue={points.length === 1 ? points[0].id : ""}>
                <option value="" disabled>Selecciona un punto</option>
                {points.map((point) => <option value={point.id} key={point.id}>{point.name}</option>)}
              </select>
            </div>
            <div className="public-quote-fields">
              <div className="field">
                <label htmlFor="public-quote-size">Tamaño</label>
                <select id="public-quote-size" name="size" defaultValue="PEQUENO" disabled={quoteTask.busy}><SizeOptions /></select>
              </div>
              <Field label="Plazo en horas">
                <input name="hours" type="number" min={1} step={1} defaultValue={24} disabled={quoteTask.busy} required />
              </Field>
            </div>
            <button type="submit" className="secondary" disabled={quoteTask.busy}>Calcular importe</button>
          </form>}
          <Status {...quoteTask} />
          {quote && <div className="receipt public-quote-result" role="status">
            <strong>Bs {quote.amount}</strong>
            <span>Importe de referencia para {quote.duration_hours} {quote.duration_hours === 1 ? "hora" : "horas"}.</span>
          </div>}
        </div>
      </div>
    </section>
    {trackingSection}
  </div>;
}
