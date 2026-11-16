import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../dist/web");
const api = new URL(process.env.BUZON_PREVIEW_API || "https://buzon-xpress.tail1a7cca.ts.net");
if (api.protocol !== "https:" && api.hostname !== "127.0.0.1") throw new Error("Invalid development service origin.");
const mime = { ".html": "text/html; charset=utf-8", ".js": "application/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".ttf": "font/ttf", ".woff": "font/woff", ".woff2": "font/woff2", ".json": "application/json" };
const server = http.createServer(async (request, response) => {
  try {
    const path = new URL(request.url, "http://127.0.0.1").pathname;
    if (path.startsWith("/api/v1/")) {
      const chunks = []; let size = 0;
      for await (const chunk of request) { size += chunk.length; if (size > 65536) { response.writeHead(413).end(); return; } chunks.push(chunk); }
      const headers = {};
      for (const name of ["content-type", "accept", "authorization", "idempotency-key"]) if (request.headers[name]) headers[name] = request.headers[name];
      const target = new URL(request.url, api);
      const result = await fetch(target, { method: request.method, headers, redirect: "error", signal: AbortSignal.timeout(18000),
        ...(!["GET", "HEAD"].includes(request.method) ? { body: Buffer.concat(chunks) } : {}) });
      response.writeHead(result.status, { "Content-Type": result.headers.get("content-type") || "application/json", "Cache-Control": "no-store" });
      response.end(Buffer.from(await result.arrayBuffer())); return;
    }
    let file = resolve(root, "." + decodeURIComponent(path));
    if (file !== root && !file.startsWith(root + sep)) { response.writeHead(403).end(); return; }
    try { if (!(await stat(file)).isFile()) file = resolve(root, "index.html"); }
    catch { file = resolve(root, "index.html"); }
    const extension = file.slice(file.lastIndexOf("."));
    response.writeHead(200, { "Content-Type": mime[extension] || "application/octet-stream", "Cache-Control": "no-cache",
      "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer" });
    response.end(await readFile(file));
  } catch {
    response.writeHead(503, { "Content-Type": "application/json", "Cache-Control": "no-store" });
    response.end(JSON.stringify({ code: "SERVICIO_NO_DISPONIBLE", message: "No se pudo conectar. Vuelve a intentarlo." }));
  }
});
server.listen(Number(process.env.BUZON_PREVIEW_PORT || 8082), "127.0.0.1", () => {
  console.log("BUZON Xpress mobile preview: http://127.0.0.1:" + server.address().port);
});
