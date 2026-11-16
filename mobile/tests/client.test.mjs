import assert from "node:assert/strict";
import { test } from "node:test";
import { ApiError, BuzonClient } from "../src/api/client.ts";

function client(fetcher, onUnauthorized) {
  return new BuzonClient({ baseUrl: "https://buzon.example", fetcher, uuid: () => crypto.randomUUID(), onUnauthorized });
}
test("el acceso nativo no envía cookies, origen ni credenciales de sesión anteriores", async () => {
  let options;
  const api = client(async (url, init) => { assert.equal(url, "https://buzon.example/api/v1/mobile/auth/login"); options = init; return Response.json({ mfa_required: true }); });
  api.setToken("mob_" + "x".repeat(43));
  await api.login("persona@example.com", "a private phrase");
  assert.equal(options.credentials, "omit");
  assert.equal(options.headers.Authorization, undefined);
  assert.equal(options.headers.Cookie, undefined);
  assert.equal(options.headers.Origin, undefined);
  assert.deepEqual(JSON.parse(options.body), { email: "persona@example.com", password: "a private phrase" });
});
test("las consultas privadas usan el portador y una expiración fuerza a volver a entrar", async () => {
  let expired = false;
  const api = client(async (_url, options) => {
    assert.equal(options.headers.Authorization, "Bearer mob_" + "x".repeat(43));
    return Response.json({ code: "SESION_INVALIDA", message: "Inicia sesión." }, { status: 401 });
  }, () => { expired = true; });
  api.setToken("mob_" + "x".repeat(43));
  await assert.rejects(api.me(), error => error instanceof ApiError && error.status === 401);
  assert.equal(expired, true);
});
test("las consultas públicas no envían la sesión", async () => {
  const api = client(async (_url, options) => { assert.equal(options.headers.Authorization, undefined); return Response.json([]); });
  api.setToken("mob_" + "x".repeat(43));
  await api.points();
});
test("una respuesta incierta conserva la clave y el siguiente éxito libera la operación", async () => {
  const keys = [];
  const api = client(async (_url, options) => {
    keys.push(options.headers["Idempotency-Key"]);
    if (keys.length === 1) throw new TypeError("disconnect");
    return Response.json({ id: "synthetic" });
  });
  api.setToken("mob_" + "x".repeat(43));
  const send = api.mutation();
  await assert.rejects(send("/custodies", { description: "Caja" }));
  await send("/custodies", { description: "Caja" });
  await send("/custodies", { description: "Caja" });
  assert.equal(keys[0], keys[1]); assert.notEqual(keys[1], keys[2]);
});
test("una confirmación ilegible se trata como incierta", async () => {
  const keys = [];
  const api = client(async (_url, options) => {
    keys.push(options.headers["Idempotency-Key"]);
    return keys.length === 1 ? new Response("invalid", { status: 200 }) : Response.json({});
  });
  api.setToken("mob_" + "x".repeat(43));
  const send = api.mutation();
  await assert.rejects(send("/custodies", {}), error => error.code === "RESPUESTA_INCIERTA");
  await send("/custodies", {});
  assert.equal(keys[0], keys[1]);
});

test("una respuesta tardía de una sesión anterior no revoca la nueva", async () => {
  let unauthorized = 0;
  let respond;
  const headers = [];
  const client = new BuzonClient({
    baseUrl: "https://api.example",
    uuid: () => "test",
    onUnauthorized: () => unauthorized++,
    fetcher: async (_, init) => {
      headers.push(init.headers.Authorization);
      if (headers.length === 1) return new Promise(resolve => { respond = resolve; });
      return new Response(JSON.stringify({ id: "user" }), { status: 200 });
    },
  });
  client.setToken("anterior");
  const pending = client.me();
  client.setToken("nueva");
  respond(new Response(JSON.stringify({ message: "Sesión terminada." }), { status: 401 }));
  await assert.rejects(pending, error => error.status === 401);
  assert.equal(unauthorized, 0);
  await client.me();
  assert.deepEqual(headers, ["Bearer anterior", "Bearer nueva"]);
});

test("una respuesta sin estructura no muestra errores internos ni confirma operaciones", async () => {
  for (const body of ["null", "true", "42"]) {
    const client = new BuzonClient({ baseUrl: "", uuid: () => "test", fetcher: async () => new Response(body) });
    await assert.rejects(client.points(), error => error.code === "RESPUESTA_INCIERTA");
  }
});
