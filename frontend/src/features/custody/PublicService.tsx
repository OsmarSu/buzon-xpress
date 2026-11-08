import { useEffect, useState } from "react";

import { custodyApi, type Point } from "../../services/custody";
import { Field, formData, Schedule, Status, useTask, value } from "../shared/forms";

const trackingLabels = { PENDIENTE: "Pendiente", RECIBIDA: "Recibida", FINALIZADA: "Finalizada" };

export function PublicService({ initialReference }: { initialReference: string | null }) {
  const [points, setPoints] = useState<Point[]>([]);
  const [result, setResult] = useState<Awaited<ReturnType<typeof custodyApi.tracking>>>();
  const pointsTask = useTask();
  const tracking = useTask();

  function loadPoints() {
    void pointsTask.run(async () => setPoints(await custodyApi.points()));
  }

  useEffect(loadPoints, []);

  return <div className="public-grid">
    <section aria-labelledby="tracking-heading">
      <h2 id="tracking-heading">Consultar estado público</h2>
      <p>Usa la referencia pública que compartió un participante.</p>
      <form onSubmit={(event) => {
        const reference = value(formData(event), "reference");
        setResult(undefined);
        void tracking.run(async () => setResult(await custodyApi.tracking(reference)));
      }}>
        <Field label="Referencia pública">
          <input name="reference" defaultValue={initialReference ?? ""} autoComplete="off" required maxLength={180} />
        </Field>
        <button type="submit" disabled={tracking.busy}>Consultar estado</button>
      </form>
      <Status {...tracking} />
      {result && <div className="receipt" aria-live="polite">
        <strong>{trackingLabels[result.state]}</strong>
        <p>{result.point_name}</p>
        <Schedule hours={result.opening_hours} />
      </div>}
    </section>
    <section aria-labelledby="points-heading">
      <h2 id="points-heading">Puntos y horarios</h2>
      <Status {...pointsTask} />
      {points.length > 0 ? <ul className="items">{points.map((point) =>
        <li key={point.id}>
          <strong>{point.name}</strong><p>{point.address}</p><Schedule hours={point.opening_hours} />
        </li>,
      )}</ul> : !pointsTask.busy && !pointsTask.error && <p>Actualmente no hay puntos activos.</p>}
      {pointsTask.error && <button type="button" onClick={loadPoints}>Volver a consultar</button>}
    </section>
  </div>;
}
