import { rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const targets = [
  join(root, "..", "src", "api", "model"),
  join(root, "..", "src", "api", "zod"),
];

for (const target of targets) {
  rmSync(target, { force: true, recursive: true });
}
