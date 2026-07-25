/**
 * Launch Mastra Studio (mastra dev) with the repo-root .env loaded.
 *
 * Studio bundles the app before running it, and the bundler drops a bare
 * side-effect import, so env.ts does not run inside Studio the way it does in the
 * step scripts. Instead we load the key into this process here, then start the dev
 * server as a child that inherits the environment. Run it with npm run dev.
 */

import "../env.ts";
import { spawn } from "node:child_process";

spawn("mastra", ["dev"], {
  stdio: "inherit",
  shell: true,
  env: { ...process.env, NODE_OPTIONS: "--disable-warning=ExperimentalWarning" },
});
