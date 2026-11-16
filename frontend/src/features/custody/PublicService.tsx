import { useEffect, useRef, useState } from "react";

import { custodyApi, type Point, type Quote, type Size } from "../../services/custody";
import { Field, formData, Schedule, SizeGuide, SizeOptions, Status, useTask, value } from "../shared/forms";

const trackingLabels = {
  PENDIENTE: "Pendiente de recepción",
  RECIBIDA: "En custodia",
  FINALIZADA: "Finalizada",
};

export function PublicTracking({ initialReference }: { initialReference: string | null }) {
  const [result, setResult] = useState<Awaited<ReturnType<typeof custodyApi.tracking>>>();
  const trackingHeading = useRef<HTMLHeadingElement>(null);
  const tracking = useTask();

  useEffect(() => {
    if (initialReference) trackingHeading.current?.focus();
  }, [initialReference]);

  return <section id="seguimiento" className="public-chapter public-tracking" data-public-section tabIndex={-1} aria-labelledby="tracking-heading">
    <div className="public-layout public-tracking-grid">
    <div className="public-section-intro" data-reveal>
      <p className="public-eyebrow">04 / Siempre informado</p>
      <h2 id="tracking-heading" ref={trackingHeading} tabIndex={-1}>Seguimiento</h2>
      <p id="tracking-hint">Usa el código público de seguimiento que te compartieron al registrar la custodia para consultar su estado, punto y horario.</p>
    </div>
    <div className="public-tracking-panel" data-reveal>
      <form aria-busy={tracking.busy} onSubmit={(event) => {
        const reference = value(formData(event), "reference");
        setResult(undefined);
        void tracking.run(async () => setResult(await custodyApi.tracking(reference)));
      }}>
        <Field label="Código público de seguimiento" hint={"Pega el código público de seguimiento que te compartieron para consultar el estado."} example={"El emisor puede compartir el código público de seguimiento de su registro. Copia el código completo, sin espacios adicionales."}>
          <input name="reference" defaultValue={initialReference ?? ""} autoComplete="off"
            spellCheck={false} placeholder="Pega aquí el código completo" aria-describedby="tracking-hint" required maxLength={180} />
        </Field>
        <button type="submit" disabled={tracking.busy}>{tracking.busy && <span className="public-loading-dot" aria-hidden="true" />}{tracking.busy ? "Consultando…" : "Consultar estado"}</button>
      </form>
      <Status {...tracking} />
      {result && <div className="receipt public-tracking-result" aria-live="polite">
        <strong>{trackingLabels[result.state]}</strong>
        <p>{result.point_name}</p>
        <Schedule hours={result.opening_hours} />
      </div>}
    </div>
    </div>
  </section>;
}

export function PublicPoints() {
  const [points, setPoints] = useState<Point[]>([]);
  const [showAllPoints, setShowAllPoints] = useState(false);
  const [quote, setQuote] = useState<Quote>();
  const pointsTask = useTask();
  const quoteTask = useTask();

  function loadPoints() {
    void pointsTask.run(async () => setPoints(await custodyApi.points()));
  }

  useEffect(() => {
    loadPoints();
  }, []);

  return <section id="puntos" className="public-chapter public-points" data-public-section tabIndex={-1} aria-labelledby="points-heading">
    <div className="public-layout public-chapter-content">
    <div className="public-section-intro" data-reveal>
      <p className="public-eyebrow">03 / Planifica tu visita</p>
      <h2 id="points-heading">Puntos y tarifas</h2>
      <p>Compara ubicaciones, horarios y tarifas según el plazo que necesitas.</p>
    </div>
    <div className="public-service-grid">
      <div className="public-point-list">
        <Status {...pointsTask} />
        {pointsTask.busy && points.length === 0 && <div className="public-points-skeleton" aria-hidden="true">
          {[1, 2, 3].map((item) => <div key={item}><span /><span /><span /></div>)}
        </div>}
        {points.length > 0 ? <ul className="public-point-items">
          {points.slice(0, showAllPoints ? points.length : 4).map((point) => <li key={point.id}>
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
        {points.length > 4 && <button type="button" className="secondary public-points-toggle"
          onClick={() => setShowAllPoints((show) => !show)} aria-expanded={showAllPoints}>
          {showAllPoints ? "Mostrar menos puntos" : "Ver los " + points.length + " puntos"}
        </button>}
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
              <SizeGuide />
            </div>
            <Field label="Plazo en horas" example={"24 equivale a un día; 48, a dos días. La estimación se calcula con horas enteras."}>
              <input name="hours" type="number" min={1} step={1} defaultValue={24} disabled={quoteTask.busy} required />
            </Field>
          </div>
          <button type="submit" className="secondary" disabled={quoteTask.busy}>{quoteTask.busy && <span className="public-loading-dot" aria-hidden="true" />}{quoteTask.busy ? "Calculando…" : "Calcular importe"}</button>
        </form>}
        <Status {...quoteTask} />
        {quote && <div className="receipt public-quote-result" role="status">
          <strong>Bs {quote.amount}</strong>
          <span>Importe de referencia para {quote.duration_hours} {quote.duration_hours === 1 ? "hora" : "horas"}.</span>
        </div>}
      </div>
    </div>
    </div>
  </section>;
}
