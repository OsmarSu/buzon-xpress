import assert from "node:assert/strict";
import { test } from "node:test";

import { ApiError, mutate, mutationSeries } from "../src/services/api.ts";

test("la mutación envía CSRF, cookie de origen y método explícito", async (context) => {
  const mock = context.mock.method(globalThis, "fetch", async (url) =>
    url.endsWith("/csrf") ? Response.json({ csrf_token: "synthetic" }) : Response.json({ id: "r1" }));
  const payload = { state: "DISPONIBLE" };
  await mutate("/admin/locations/r1", payload, { method: "PATCH", key: "synthetic-key" });
  const [[csrfPath, csrfOptions], [path, options]] = mock.mock.calls.map((call) => call.arguments);
  assert.equal(csrfPath, "/api/v1/auth/csrf");
  assert.equal(csrfOptions.cache, "no-store");
  assert.equal(path, "/api/v1/admin/locations/r1");
  assert.equal(options.credentials, "same-origin");
  assert.equal(options.method, "PATCH");
  assert.deepEqual(options.headers, {
    "X-CSRF-Token": "synthetic", "Content-Type": "application/json", "Idempotency-Key": "synthetic-key",
  });
  assert.equal(options.body, JSON.stringify(payload));
});

test("un fallo ambiguo mantiene la clave y una respuesta definitiva abre otro intento", async (context) => {
  const keys = [];
  context.mock.method(globalThis, "fetch", async (url, options) => {
    if (url.endsWith("/csrf")) return Response.json({ csrf_token: "synthetic" });
    keys.push(options.headers["Idempotency-Key"]);
    if (keys.length === 1) throw new TypeError("synthetic disconnect");
    if (keys.length === 3) return Response.json({
      code: "VERSION", message: "Cambia la versión", correlation_id: "correlation-123",
    }, { status: 409 });
    return Response.json({ id: "r1" });
  });
  const send = mutationSeries();
  const route = "/custodies/r1/handover";
  await assert.rejects(send(route, { expected_version: 1 }), { code: "SIN_CONEXION" });
  await send(route, { expected_version: 1 });
  await assert.rejects(send(route, { expected_version: 1 }), (error) =>
    error instanceof ApiError && error.status === 409 && error.correlationId === "correlation-123");
  await send(route, { expected_version: 2 });
  assert.equal(keys[0], keys[1]);
  assert.notEqual(keys[1], keys[2]);
  assert.notEqual(keys[2], keys[3]);
  assert.ok(keys.every((key) => key.length >= 16));
});

test("un rechazo confirmado de credencial permite un intento posterior distinto", async (context) => {
  const keys = [];
  context.mock.method(globalThis, "fetch", async (url, options) => {
    if (url.endsWith("/csrf")) return Response.json({ csrf_token: "synthetic" });
    keys.push(options.headers["Idempotency-Key"]);
    return Response.json({ message: "Inválido" }, { status: 422 });
  });
  const send = mutationSeries();
  await assert.rejects(send("/custodies/r1/verify", { code: "000000" }));
  await assert.rejects(send("/custodies/r1/verify", { code: "000000" }));
  assert.notEqual(keys[0], keys[1]);
});

test("una confirmación mantiene la clave aunque el servidor responda que sigue pendiente", async (context) => {
  const keys = [];
  context.mock.method(globalThis, "fetch", async (url, options) => {
    if (url.endsWith("/csrf")) return Response.json({ csrf_token: "synthetic" });
    keys.push(options.headers["Idempotency-Key"]);
    return keys.length === 1
      ? Response.json({ code: "EN_CURSO", message: "Aún en curso" }, { status: 409 })
      : Response.json({ id: "receipt" });
  });
  const confirm = mutationSeries();
  const payload = { authorization_id: "auth", expected_version: 2, physically_delivered: true };
  await assert.rejects(confirm("/custodies/r1/handover", payload), { status: 409 });
  await confirm("/custodies/r1/handover", payload);
  assert.equal(keys[0], keys[1]);
});

test("un cuerpo exitoso pero ilegible se trata como confirmación incierta", async (context) => {
  context.mock.method(globalThis, "fetch", async (url) =>
    url.endsWith("/csrf") ? Response.json({ csrf_token: "synthetic" }) :
      new Response("not json", { status: 200, headers: { "X-Correlation-ID": "receipt-reference" } }));
  await assert.rejects(mutate("/custodies/r1/handover", { expected_version: 2 }), (error) =>
    error instanceof ApiError && error.status === 0 && error.correlationId === "receipt-reference");
});
