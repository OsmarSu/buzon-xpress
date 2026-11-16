import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const queryString = require("query-string");
test("el decodificador corregido conserva los parámetros usados por Expo Router", () => {
  const result = queryString.parse("nombre=Mar%C3%ADa+L%C3%B3pez&id=d8ae67be-7c44-4e07-881d-ff34d7293f14&invalido=%zz");
  assert.equal(result.nombre, "María López");
  assert.equal(result.id, "d8ae67be-7c44-4e07-881d-ff34d7293f14");
  assert.equal(result.invalido, "%zz");
  assert.equal(queryString.stringify({ referencia: "a/b+c" }), "referencia=a%2Fb%2Bc");
});
