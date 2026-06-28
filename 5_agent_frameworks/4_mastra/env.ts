/**
 * Load the repo-root .env, the same one the Python days use.
 *
 * Node's dotenv only looks in the current directory, but the course keeps a
 * single .env at the repo root and runs each day from its own folder. So we
 * search upward from the working directory for the nearest .env and load it,
 * the same thing Python's load_dotenv does. Import this first from any script
 * that talks to a model: import "../env.ts".
 */

import { config } from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

function findEnv(start = process.cwd()): string | undefined {
  let dir = start;
  while (true) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) return candidate;
    const parent = dirname(dir);
    if (parent === dir) return undefined;
    dir = parent;
  }
}

config({ path: findEnv(), override: true, quiet: true });
