import { useState } from "react";

import { ApiError } from "../../services/api";
import { custodyApi, custodyPath, sizeLabel, type Authorization, type Custody, type Handover, type Location, type Point, type Quote } from "../../services/custody";
import { CustodySummary } from "../custody/Participant";
import { CustodyExceptions, Returns } from "./Exceptions";
import { AuthorizedHandover, Receipt } from "./Handover";
import { Field, formData, payment, PaymentFields, Status, useMutation, useTask, value } from "../shared/forms";

const physicalCheck = "COMPROBACION_VISUAL_COMPLETADA";

function QuoteFields({ quote }: { quote: Quote }) {
  return <>
    <p role="status">Tarifa calculada de {quote.amount} BOB por {quote.duration_hours} horas.</p>
    <label className="check"><input type="checkbox" required /> Acepto el importe indicado</label>
    <PaymentFields />
  </>;
}

function Reception({ custody, inventory, onReceive }: {
  custody: Custody; inventory: Location[]; onReceive: (next: Custody) => void;
}) {
  const task = useTask();
  const send = useMutation();
  const [hours, setHours] = useState("24");
  const [quote, setQuote] = useState<Quote>();
  const available = inventory.filter((item) => item.state === "DISPONIBLE" && item.size_category === custody.size_category);

  return <>
    <h3>Confirmar recepción</h3>
    <p>Comprueba el bulto y registra el cobro y la ubicación en la misma operación.</p>
    {!available.length && <p>No hay una ubicación libre del tamaño declarado en el inventario consultado.</p>}
    <form onSubmit={(event) => {
      const data = formData(event);
      if (!quote) return;
      void task.run(async () => onReceive(await send<Custody>(custodyPath(custody.id, "receive"), {
        location_id: value(data, "location"),
        expected_version: custody.version,
        duration_hours: quote.duration_hours,
        tariff_id: quote.tariff_id,
        accepted_amount: quote.amount,
        external_condition: value(data, "condition"),
        ...payment(data),
      })));
    }} aria-busy={task.busy}>
      <Field label="Condición externa del objeto">
        <textarea name="condition" required maxLength={255} />
      </Field>
      <Field label="Ubicación disponible">
        <select name="location" required disabled={!available.length}>
          <option value="">Elige una ubicación</option>
          {available.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}
        </select>
      </Field>
      <Field label="Plazo inicial en horas">
        <input type="number" min={1} step={1} value={hours} disabled={task.busy}
          onChange={(event) => { setHours(event.target.value); setQuote(undefined); }} />
      </Field>
      <button type="button" className="secondary" disabled={task.busy || !Number.isInteger(Number(hours)) || Number(hours) < 1}
        onClick={() => void task.run(async () => setQuote(await custodyApi.quote(custody.point_id, custody.size_category, Number(hours))))}>
        Calcular importe de recepción
      </button>
      {quote && <QuoteFields key={quote.tariff_id + quote.duration_hours} quote={quote} />}
      <button type="submit" disabled={task.busy || !quote || !available.length}>Confirmar recepción</button>
    </form>
    <Status {...task} />
  </>;
}

function Extension({ custody, onUpdate }: { custody: Custody; onUpdate: (next: Custody) => void }) {
  const task = useTask();
  const send = useMutation();
  const [hours, setHours] = useState("24");
  const [quote, setQuote] = useState<Quote>();
  const [notice, setNotice] = useState("");

  return <details>
    <summary>Registrar prórroga</summary>
    <form onSubmit={(event) => {
      const data = formData(event);
      if (!quote) return;
      void task.run(async () => {
        onUpdate(await send<Custody>(custodyPath(custody.id, "extend"), {
          additional_hours: quote.duration_hours,
          expected_version: custody.version,
          accepted_amount: quote.amount,
          ...payment(data),
        }));
        setQuote(undefined);
        setNotice("Prórroga registrada.");
      });
    }} aria-busy={task.busy}>
      <Field label="Horas adicionales">
        <input type="number" min={1} step={1} value={hours} disabled={task.busy}
          onChange={(event) => { setHours(event.target.value); setQuote(undefined); }} />
      </Field>
      <button type="button" className="secondary" disabled={task.busy || !Number.isInteger(Number(hours)) || Number(hours) < 1}
        onClick={() => void task.run(async () =>
          setQuote(await custodyApi.quote(custody.point_id, custody.size_category, Number(hours), custody.id)))}>
        Calcular importe de prórroga
      </button>
      {quote && <QuoteFields key={quote.tariff_id + quote.duration_hours} quote={quote} />}
      <button type="submit" disabled={task.busy || !quote}>Registrar prórroga y cobro</button>
    </form>
    <Status {...task} message={notice} />
  </details>;
}

function Pickup({ custody, onUpdate, onInventoryChange, onRefresh }: {
  custody: Custody; onUpdate: (next: Custody) => void; onInventoryChange: () => void; onRefresh: () => void;
}) {
  const task = useTask();
  const send = useMutation();
  const [authorization, setAuthorization] = useState<Authorization>();
  const [receipt, setReceipt] = useState<Handover>();
  const [message, setMessage] = useState("");

  if (receipt) return <Receipt handover={receipt} />;
  if (authorization) return <AuthorizedHandover authorization={authorization} kind="RETIRO"
    onConfirmed={(result) => {
      setReceipt(result);
      setAuthorization(undefined);
      onRefresh();
      onInventoryChange();
    }}
    onAborted={(result) => {
      setAuthorization(undefined);
      onUpdate(result);
      setMessage("Preparación anulada. La custodia sigue en el punto.");
    }} />;

  if (custody.state === "RETIRO_EN_CURSO") return <p className="warning">
    Hay un retiro en curso. Comprueba si ya hubo entrega y continúa mediante la conciliación del punto.
  </p>;
  if (custody.state !== "EN_CUSTODIA") return null;
  return <details>
    <summary>Verificar autorización de retiro</summary>
    <form onSubmit={(event) => {
      const form = event.currentTarget;
      const data = formData(event);
      void task.run(async () => {
        const result = await send<Authorization>(custodyPath(custody.id, "verify"), {
          code: value(data, "code"),
          expected_version: custody.version,
          recipient_check: physicalCheck,
        });
        form.reset();
        setAuthorization(result);
        onUpdate({ ...custody, state: "RETIRO_EN_CURSO", version: result.version });
      });
    }} aria-busy={task.busy}>
      <Field label="Código de retiro de seis dígitos">
        <input type="password" name="code" inputMode="numeric" autoComplete="off" pattern="[0-9]{6}" required maxLength={6} />
      </Field>
      <label className="check"><input type="checkbox" required /> Comprobación visual del destinatario completada</label>
      <button type="submit" disabled={task.busy}>Verificar autorización</button>
    </form>
    <Status {...task} message={message} />
  </details>;
}

export function Operations({ points }: { points: Point[] }) {
  const pointTask = useTask();
  const custodyTask = useTask();
  const [point, setPoint] = useState<Point>();
  const [inventory, setInventory] = useState<Location[]>([]);
  const [selectedCustody, setCustody] = useState<Custody>();
  const custody = selectedCustody?.point_id === point?.id ? selectedCustody : undefined;
  const [message, setMessage] = useState("");

  function updateInventory() {
    if (point) void pointTask.run(async () => setInventory(await custodyApi.inventory(point.id)));
  }

  return <>
    <section aria-labelledby="operation-point-heading">
      <h2 id="operation-point-heading">Terminal de operación</h2>
      <form onSubmit={(event) => {
        const pointId = value(formData(event), "point");
        const selected = points.find((item) => item.id === pointId);
        if (!selected) return;
        void pointTask.run(async () => {
          const locations = await custodyApi.inventory(pointId);
          if (point?.id !== pointId) setCustody(undefined);
          setPoint(selected);
          setInventory(locations);
        });
      }}>
        <Field label="Punto de trabajo">
          <select name="point" required disabled={pointTask.busy} defaultValue="">
            <option value="">Elige un punto</option>
            {points.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </Field>
        <button type="submit" disabled={pointTask.busy || !points.length}>Abrir terminal del punto</button>
      </form>
      <Status {...pointTask} message={point ? "Punto autorizado · " + point.name : undefined} />
    </section>

    {point && <div className="dashboard-grid">
      <section aria-labelledby="find-custody-heading">
        <h2 id="find-custody-heading">Localizar custodia</h2>
        <form onSubmit={(event) => {
          const data = formData(event);
          const query = value(data, "query");
          const mode = value(data, "mode");
          setMessage("");
          void custodyTask.run(async () => {
            const result = mode === "id" ? await custodyApi.detail(query)
              : (await custodyApi.list({ point_id: point.id, tracking_number: query }))[0];
            if (!result || result.point_id !== point.id) {
              throw new ApiError(404, "CUSTODIA_NO_ENCONTRADA", "No se encontró una custodia en el punto activo.");
            }
            setCustody(result);
          });
        }}>
          <Field label="Buscar por">
            <select name="mode"><option value="tracking">Guía privada</option><option value="id">Identificador de custodia</option></select>
          </Field>
          <Field label="Guía o identificador"><input name="query" required autoComplete="off" maxLength={128} /></Field>
          <button type="submit" disabled={custodyTask.busy}>Consultar custodia del punto</button>
        </form>
        <Status {...custodyTask} message={message} />
        {custody && <div className="actions">
          <button className="secondary" type="button" disabled={custodyTask.busy} onClick={() => void custodyTask.run(async () =>
            setCustody(await custodyApi.detail(custody.id)))}>Actualizar estado y versión</button>
          <button className="secondary" type="button" onClick={() => setCustody(undefined)}>Cerrar detalle</button>
        </div>}
      </section>

      <section aria-labelledby="inventory-heading">
        <h2 id="inventory-heading">Inventario del punto</h2>
        <button type="button" className="secondary" onClick={updateInventory} disabled={pointTask.busy}>Actualizar inventario</button>
        <ul className="items">{inventory.map((item) => <li key={item.id}>
          <strong>{item.code}</strong> · {sizeLabel[item.size_category]} · {item.state.replaceAll("_", " ").toLowerCase()}
        </li>)}</ul>
        {!inventory.length && <p>El punto no tiene ubicaciones registradas.</p>}
      </section>

      {custody && <section className="full-width" aria-labelledby="operation-custody-heading">
        <h2 id="operation-custody-heading">Operar custodia</h2>
        <CustodySummary custody={custody} point={point} />
        {custody.state === "REGISTRADA" && <Reception key={"reception-" + custody.id} custody={custody} inventory={inventory}
          onReceive={(result) => {
            setCustody(result);
            setMessage("Recepción, ubicación y cobro registrados.");
            updateInventory();
          }} />}
        <Pickup key={"pickup-" + custody.id} custody={custody} onUpdate={setCustody} onInventoryChange={updateInventory} onRefresh={() => void custodyTask.run(async () => setCustody(await custodyApi.detail(custody.id)))} />
        <Returns key={"returns-" + custody.id} custody={custody}
          onAuthorized={(result) => setCustody({ ...custody, state: "DEVOLUCION_EN_CURSO", version: result.version })}
          onReturned={() => {
            void custodyTask.run(async () => setCustody(await custodyApi.detail(custody.id)));
            updateInventory();
          }} />
        <CustodyExceptions key={"custodyexceptions-" + custody.id} custody={custody} />
        {custody.state === "EN_CUSTODIA" && <Extension key={"extension-" + custody.id} custody={custody} onUpdate={setCustody} />}
      </section>}
    </div>}
  </>;
}
