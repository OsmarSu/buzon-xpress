// query-string 7 consumes a CommonJS decoder; the fixed decoder exposes an ESM default.
import { createRequire } from "node:module";
import { readFile, writeFile } from "node:fs/promises";
const require = createRequire(import.meta.url);
const path = require.resolve("query-string");
const original = "const decodeComponent = require('decode-uri-component');";
const replacement = "const decodeModule = require('decode-uri-component');\nconst decodeComponent = typeof decodeModule === 'function' ? decodeModule : decodeModule.default;";
const source = await readFile(path, "utf8");
if (source.includes(original)) await writeFile(path, source.replace(original, replacement));
else if (!source.includes(replacement)) throw new Error("Revisar la compatibilidad del decodificador al actualizar Expo Router.");
