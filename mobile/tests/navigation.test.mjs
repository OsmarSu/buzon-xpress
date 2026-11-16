import test from "node:test";
import assert from "node:assert/strict";
import { safeReturnPath, custodyId, registrationDraft } from "../src/navigation/paths.ts";
test("el retorno de acceso acepta solo pantallas internas conocidas", () => {
  assert.equal(safeReturnPath("/custodias"), "/custodias");
  for (const candidate of ["https://otro.example", "//otro.example", "/custodias?token=algo", "/acceso", ["/cuenta"], undefined]) assert.equal(safeReturnPath(candidate), "/");
});
test("los enlaces a custodias aceptan identificadores válidos sin datos adicionales", () => {
  const id = "d8ae67be-7c44-4e07-881d-ff34d7293f14";
  assert.equal(custodyId(id), id);
  for (const candidate of ["../cuenta", id + "?token=algo", [id], undefined]) assert.equal(custodyId(candidate), undefined);
});

test("Puntos conserva el punto y tamaño y normaliza las horas al preparar el registro", () => {
  const id = "d8ae67be-7c44-4e07-881d-ff34d7293f14";
  assert.deepEqual(registrationDraft(id, "MEDIANO", "000024"), { pointId: id, size: "MEDIANO", hours: "24" });
});
test("un enlace de prerregistro rechaza parámetros ambiguos o inválidos", () => {
  const id = "d8ae67be-7c44-4e07-881d-ff34d7293f14";
  for (const point of ["../cuenta", id + "?token=algo", [id], undefined]) assert.equal(registrationDraft(point, "PEQUENO", "24"), undefined);
  for (const size of ["otro", ["GRANDE"], undefined]) assert.equal(registrationDraft(id, size, "24"), undefined);
  for (const hours of ["0", "-1", "1.5", "1e3", "1000000", " 24 ", ["24"], undefined]) assert.equal(registrationDraft(id, "GRANDE", hours), undefined);
});
