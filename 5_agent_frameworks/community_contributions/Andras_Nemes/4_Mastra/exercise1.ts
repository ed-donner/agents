/**
 * Exercise part 1: a different goal.
 *
 * This is step5.ts from the lab with two changes: the goal on the board is new
 * (a haiku instead of the translation), and an onStepFinish callback borrowed
 * from worker.ts prints each tool call as the loop makes it, so you can watch
 * the agent plan, write the file and tick its steps off in the terminal.
 *
 * board.ts and tools.ts are unchanged copies of the lab's files. Their paths
 * derive from their own location, so this folder gets its own board.sqlite and
 * its own workspace, leaving the lab's untouched. Run it with: npm run exercise1
 */

import "./env.ts";
import { join } from "node:path";
import { mkdirSync, rmSync, existsSync, readFileSync } from "node:fs";
import { Agent } from "@mastra/core/agent";
import { boardTools, makeFilesystem, WORKSPACE } from "./tools.ts";
import { resetBoard, addGoal, claimTodo, showBoard } from "./board.ts";

const GOAL = "Write a short haiku about Madrid into madrid.txt.";

const INSTRUCTIONS = `
You are a careful worker with a shared todo board and a set of file tools.

Take the pending goal and see it through. Begin by laying out a short plan: the handful of concrete steps the work itself breaks down into, added to the board under the goal. Then carry them out with your file tools, marking each step done as you finish it. Once the steps are all done, close the goal. Your files live in the single folder your tools are allowed to use.
`;

// Seed the board with the one goal and clear any old output.
mkdirSync(WORKSPACE, { recursive: true });
rmSync(join(WORKSPACE, "madrid.txt"), { force: true });
resetBoard();
const goalId = addGoal(GOAL);
claimTodo(goalId); // the worker picks up the goal: pending -> in_progress
console.log(`Seeded goal ${goalId}: ${GOAL}\n`);

const filesystem = makeFilesystem();
const worker = new Agent({
  id: "worker",
  name: "Worker",
  instructions: INSTRUCTIONS,
  model: "openai/gpt-5.4-mini",
  tools: { ...boardTools, ...(await filesystem.listTools()) },
});

await worker.generate("Please work the pending goal on the board.", {
  maxSteps: 25,
  onStepFinish: (step: { toolCalls?: { payload: { toolName: string; args?: unknown } }[] }) => {
    for (const call of step.toolCalls ?? []) {
      console.log(`  called ${call.payload.toolName}(${JSON.stringify(call.payload.args)})`);
    }
  },
});
await filesystem.disconnect();

console.log("\nBoard after the run:");
showBoard();
const madrid = join(WORKSPACE, "madrid.txt");
if (existsSync(madrid)) {
  console.log("\nmadrid.txt:\n" + readFileSync(madrid, "utf-8"));
}

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
