// The scoring harness: deterministic, no LLM, no browser.
//
// Each worker's logic.js is a plain script that exposes its pure functions on
// globalThis.MissionLogic. The harness evaluates that file in a small sandbox,
// calls each function with known inputs, and compares the result to the known
// physics answer within a tolerance. The output is one JSON object on stdout:
//
//   { passed, total, percent, modules: [{ key, passed, total, failures: [...] }] }
//
// Failures are written as full sentences naming the call, the value returned and
// the value expected, so the orchestrator can hand them straight to a builder as
// a fix task. Run it as: node harness.mjs <siteDir> [slug ...]

import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import vm from "node:vm";

function check(fn, args, expect, unit, tol = 0.01) {
  return { fn, args, expect, unit, tol };
}

// The known-answer test vectors, matching the contracts in prompts.py. The
// expected values follow from the formulas and constants the task text names,
// so a correct implementation passes comfortably inside the tolerance.
const SUITES = {
  strands: [
    check("deltaV", [350, 500000, 100000], 5524, "m/s"),
    check("deltaV", [300, 200000, 50000], 4078, "m/s"),
    check("deltaV", [450, 120000, 40000], 4848, "m/s"),
    check("deltaV", [311, 2970000, 970000], 3413, "m/s"),
    check("massRatioFor", [9400, 350], 15.47, "(mass ratio)"),
    check("massRatioFor", [3432.33, 350], 2.718, "(mass ratio)"),
  ],
  pydantic: [
    check("transferTimeDays", [1, 1.524], 258.9, "days", 0.02),
    check("transferTimeDays", [1, 0.723], 146.0, "days", 0.02),
    check("transferTimeDays", [1, 5.203], 997.5, "days", 0.02),
    check("transferDeltaVKms", [1, 1.524], 5.6, "km/s", 0.03),
    check("transferDeltaVKms", [1, 0.723], 5.21, "km/s", 0.03),
    check("transferDeltaVKms", [1, 5.203], 14.44, "km/s", 0.03),
  ],
  maf: [
    check("orbitalPeriodDays", [1], 365.25, "days"),
    check("orbitalPeriodDays", [0.387], 87.9, "days"),
    check("orbitalPeriodDays", [5.203], 4335, "days"),
    check("orbitalPeriodDays", [30.07], 60227, "days"),
    check("orbitalPeriodMinutes", [400], 92.4, "minutes"),
    check("orbitalPeriodMinutes", [35786], 1436, "minutes"),
  ],
  agno: [
    check("synodicPeriodDays", [365.25, 686.98], 779.9, "days"),
    check("synodicPeriodDays", [365.25, 224.7], 583.9, "days"),
    check("synodicPeriodDays", [365.25, 4332.59], 398.9, "days"),
    check("synodicPeriodDays", [224.7, 686.98], 333.9, "days"),
    check("nextWindowDays", [365.25, 686.98, 100], 679.9, "days"),
    check("nextWindowDays", [365.25, 686.98, 800], 759.9, "days"),
  ],
  mastra: [
    check("escapeVelocityKms", [5.972e24, 6371], 11.19, "km/s"),
    check("escapeVelocityKms", [7.342e22, 1737.4], 2.375, "km/s"),
    check("escapeVelocityKms", [6.417e23, 3389.5], 5.03, "km/s"),
    check("surfaceGravity", [5.972e24, 6371], 9.82, "m/s^2"),
    check("surfaceGravity", [6.417e23, 3389.5], 3.73, "m/s^2"),
    check("surfaceGravity", [7.342e22, 1737.4], 1.62, "m/s^2"),
  ],
};

function loadLogic(file) {
  // Evaluate logic.js in a sandbox. window aliases the sandbox itself, so a
  // builder that wrote window.MissionLogic instead of globalThis.MissionLogic
  // still loads; anything the script sets on its global lands on the sandbox.
  const code = readFileSync(file, "utf-8");
  const sandbox = { console };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox, { timeout: 2000 });
  return sandbox.MissionLogic ?? null;
}

function scoreModule(siteDir, slug, suite) {
  const file = join(siteDir, slug, "logic.js");
  let logic = null;
  let loadError = "";
  if (!existsSync(file)) {
    loadError = "logic.js is missing";
  } else {
    try {
      logic = loadLogic(file);
      if (!logic) loadError = "logic.js did not set globalThis.MissionLogic";
    } catch (error) {
      loadError = `logic.js could not be evaluated: ${error.message}`;
    }
  }

  let passed = 0;
  const failures = [];
  for (const c of suite) {
    const callText = `${c.fn}(${c.args.join(", ")})`;
    if (loadError) {
      failures.push(`${callText}: ${loadError}`);
      continue;
    }
    if (typeof logic[c.fn] !== "function") {
      failures.push(`${callText}: MissionLogic.${c.fn} is not a function`);
      continue;
    }
    let got;
    try {
      got = logic[c.fn](...c.args);
    } catch (error) {
      failures.push(`${callText} threw: ${error.message}`);
      continue;
    }
    const ok = typeof got === "number" && Number.isFinite(got) && Math.abs((got - c.expect) / c.expect) <= c.tol;
    if (ok) {
      passed += 1;
    } else {
      failures.push(`${callText} returned ${got}, expected about ${c.expect} ${c.unit} (within ${c.tol * 100}%)`);
    }
  }
  return { key: slug, passed, total: suite.length, failures };
}

const [siteDir, ...slugs] = process.argv.slice(2);
if (!siteDir) {
  console.error("usage: node harness.mjs <siteDir> [slug ...]");
  process.exit(2);
}
const wanted = slugs.length ? slugs : Object.keys(SUITES);
const modules = wanted.filter((slug) => SUITES[slug]).map((slug) => scoreModule(siteDir, slug, SUITES[slug]));
const passed = modules.reduce((n, m) => n + m.passed, 0);
const total = modules.reduce((n, m) => n + m.total, 0);
const percent = total ? Math.round((100 * passed) / total) : 0;
console.log(JSON.stringify({ passed, total, percent, modules }, null, 2));
