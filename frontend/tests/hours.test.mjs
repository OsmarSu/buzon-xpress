import assert from "node:assert/strict";
import { test } from "node:test";

import { hoursFromForm, scheduleText } from "../src/features/shared/hours.ts";

test("el horario general omite días vacíos y conserva los intervalos escritos", () => {
  const data = new FormData();
  data.set("weekdays", " 09:00–13:00 y 14:00–18:00 ");
  data.set("saturday", "09:00–12:00");
  data.set("sunday", " ");
  assert.deepEqual(hoursFromForm(data), {
    "Lunes a viernes": "09:00–13:00 y 14:00–18:00", "Sábado": "09:00–12:00",
  });
});

test("los horarios por día reemplazan el horario general sin publicar días cerrados", () => {
  const data = new FormData();
  data.set("weekdays", "09:00–17:00");
  data.set("saturday", "09:00–12:00");
  data.set("day_monday", "10:00–16:00");
  data.set("day_wednesday", "08:00–12:00");
  data.set("day_sunday", " ");
  assert.deepEqual(hoursFromForm(data), { "Lunes": "10:00–16:00", "Miércoles": "08:00–12:00" });
});

test("un formulario vacío no inventa horarios", () => {
  assert.deepEqual(hoursFromForm(new FormData()), {});
});

test("los horarios se presentan como texto legible sin mostrar estructuras internas", () => {
  assert.equal(scheduleText("09:00–17:00"), "09:00–17:00");
  assert.equal(scheduleText(["09:00–13:00", "14:00–18:00"]), "09:00–13:00 · 14:00–18:00");
  for (const value of [null, undefined, {}, { apertura: 9 }, []]) {
    assert.equal(scheduleText(value), "Consulta el horario con el personal del punto.");
  }
});
