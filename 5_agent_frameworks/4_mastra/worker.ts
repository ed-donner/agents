/**
 * The Mastra worker: the terminal version of step 5, plus the bits the Day 5 project
 * needs.
 *
 * Run bare (npm run worker), it seeds and works its own goal (read notes.txt,
 * translate to Spanish, write spanish.txt): plan the steps on the board, read the
 * file through the filesystem MCP server, translate, write the Spanish back, and tick
 * each step off before closing the goal. The onStepFinish callback prints each tool
 * call as it happens, so you can watch the loop turn.
 *
 * Given a task id and a shared board path, the same worker joins the Day 5 agent loop
 * instead: it points its file tools at the shared site, claims that one task, builds
 * what the task asks, and exits, leaving the rest of the board alone. The board path
 * arrives through the BOARD_PATH environment variable (board.ts reads it at import,
 * before this module runs) and the model through WORKER_MODEL, both set by the
 * orchestrator; a hand run can pass them the same way:
 *
 *   npm run worker                                             # standalone demo
 *   BOARD_PATH=<path> npx tsx worker.ts <taskId> <boardPath>   # Day 5: one shared task
 */

import "./env.ts";
import { join, dirname } from "node:path";
import { mkdirSync, rmSync, existsSync, readFileSync } from "node:fs";
import { Agent } from "@mastra/core/agent";
import { boardTools, makeFilesystem, WORKSPACE } from "./tools.ts";
import { resetBoard, addGoal, claimTodo, showBoard, BOARD_PATH } from "./board.ts";

// Day 5 mode is "<taskId> <boardPath>". Run bare (npm run worker), none of this fires.
const args = process.argv.slice(2);
const TASK_ID = args.length >= 2 ? Number(args[0]) : null;
// File tools write into this worker's own workspace when standalone, or the shared
// site (the board file's folder) when working a Day 5 task.
const WORK_DIR = TASK_ID === null ? WORKSPACE : dirname(BOARD_PATH);

const GOAL = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt.";

const INSTRUCTIONS = `
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
`;

/** Reset the board, clear any old output, and add the one goal. */
function seed(): number {
  mkdirSync(WORKSPACE, { recursive: true });
  rmSync(join(WORKSPACE, "spanish.txt"), { force: true });
  resetBoard();
  const goalId = addGoal(GOAL);
  claimTodo(goalId); // the worker picks up the goal: pending -> in_progress
  return goalId;
}

let message: string;
if (TASK_ID === null) {
  const goalId = seed();
  console.log(`Seeded goal ${goalId}: ${GOAL}\n`);
  message = "Please work the pending goal on the board.";
} else {
  claimTodo(TASK_ID); // light up this one task on the shared board
  message =
    `You have claimed task #${TASK_ID} on the shared board. Work only that task and its steps. ` +
    `When the work is built and checked, mark task #${TASK_ID} itself done with complete_task, then stop.`;
}

const filesystem = makeFilesystem(WORK_DIR);
const worker = new Agent({
  id: "worker",
  name: "Worker",
  instructions: INSTRUCTIONS,
  model: "openai/" + (process.env.WORKER_MODEL ?? "gpt-5.4-mini"),
  tools: { ...boardTools, ...(await filesystem.listTools()) },
});

await worker.generate(message, {
  maxSteps: 25,
  onStepFinish: (step: { toolCalls?: { payload: { toolName: string; args?: unknown } }[] }) => {
    if (TASK_ID !== null) return; // on Day 5 the orchestrator owns the console
    for (const call of step.toolCalls ?? []) {
      console.log(`  called ${call.payload.toolName}(${JSON.stringify(call.payload.args)})`);
    }
  },
});
await filesystem.disconnect();

if (TASK_ID === null) {
  // standalone: show the result; on Day 5 the orchestrator renders the shared board
  console.log("\nBoard after the run:");
  showBoard();
  const spanish = join(WORKSPACE, "spanish.txt");
  if (existsSync(spanish)) {
    console.log("\nspanish.txt:\n" + readFileSync(spanish, "utf-8"));
  }
}

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
