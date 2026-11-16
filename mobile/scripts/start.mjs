import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { spawn } from "node:child_process";

const require = createRequire(import.meta.url);
const manifest = require.resolve("expo/package.json");
const config = JSON.parse(await readFile(manifest, "utf8"));
const cli = resolve(dirname(manifest), config.bin.expo);
const child = spawn(process.execPath, [cli, "start", ...process.argv.slice(2)], {
  stdio: "inherit",
  env: { ...process.env, EXPO_UNSTABLE_HEADLESS: process.env.EXPO_UNSTABLE_HEADLESS || "1" },
});
child.on("exit", code => process.exit(code || 0));
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));
