import { config } from 'dotenv';
import { existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { createStep, createWorkflow } from '@mastra/core/workflows';
import { Agent } from '@mastra/core/agent';
import { createOpenAI } from '@ai-sdk/openai';
import { z } from 'zod';
import * as fs from 'fs/promises';
import { fileURLToPath } from 'node:url';
import { createTool } from '@mastra/core/tools';
import { MCPClient } from '@mastra/mcp';
import { DatabaseSync } from 'node:sqlite';
import { Mastra } from '@mastra/core';
import { LibSQLStore } from '@mastra/libsql';

function findEnv(start = process.cwd()) {
  let dir = start;
  while (true) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) return candidate;
    const parent = dirname(dir);
    if (parent === dir) return void 0;
    dir = parent;
  }
}
config({ path: findEnv(), override: true, quiet: true });

const BOARD_PATH = process.env.BOARD_PATH ?? join(dirname(fileURLToPath(import.meta.url)), "board.sqlite");
function connect(path = BOARD_PATH) {
  const db = new DatabaseSync(path);
  db.exec("PRAGMA journal_mode=WAL");
  db.exec("PRAGMA busy_timeout=5000");
  return db;
}
function resetBoard(path = BOARD_PATH) {
  const db = connect(path);
  db.exec("DROP TABLE IF EXISTS todos");
  db.exec(`CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    task TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT NOT NULL DEFAULT ''
  )`);
  db.close();
}
function addGoal(task, path = BOARD_PATH) {
  const db = connect(path);
  const id = db.prepare("INSERT INTO todos (task) VALUES (?)").run(task).lastInsertRowid;
  db.close();
  return Number(id);
}
function addStep(goalId, task, path = BOARD_PATH) {
  const db = connect(path);
  const id = db.prepare("INSERT INTO todos (parent_id, task) VALUES (?, ?)").run(goalId, task).lastInsertRowid;
  db.close();
  return Number(id);
}
function listTodos(path = BOARD_PATH) {
  const db = connect(path);
  const rows = db.prepare("SELECT id, parent_id, task, status, result FROM todos ORDER BY id").all();
  db.close();
  return rows;
}
function claimTodo(taskId, path = BOARD_PATH) {
  const db = connect(path);
  db.prepare("UPDATE todos SET status = 'in_progress' WHERE id = ?").run(taskId);
  db.close();
}
function completeTodo(taskId, result, path = BOARD_PATH) {
  const db = connect(path);
  db.prepare("UPDATE todos SET status = 'done', result = ? WHERE id = ?").run(result, taskId);
  db.close();
}
const RESET = "\x1B[0m";
const GREEN = "\x1B[32m";
const YELLOW = "\x1B[33m";
const DIM = "\x1B[2m";
const STRIKE = "\x1B[9m";
function showBoard(path = BOARD_PATH) {
  const todos = listTodos(path);
  for (const goal of todos.filter((t) => t.parent_id === null)) {
    console.log(formatLine(goal, "Goal", ""));
    for (const step of todos.filter((t) => t.parent_id === goal.id)) {
      console.log(formatLine(step, "Step", "  "));
    }
  }
}
function formatLine(todo, kind, indent) {
  const label = `${indent}${kind} #${todo.id}: ${todo.task}`;
  if (todo.status === "done") {
    const result = todo.result ? `  ${DIM}${todo.result}${RESET}` : "";
    return `${GREEN}${STRIKE}${label}${RESET}${result}`;
  }
  if (todo.status === "in_progress") return `${YELLOW}${label}${RESET}`;
  return label;
}

const WORKSPACE = join(dirname(fileURLToPath(import.meta.url)), "workspace");
const showTodos = createTool({
  id: "show_todos",
  description: "List every todo on the board. A goal has parent_id null; a step has parent_id set to its goal's id.",
  inputSchema: z.object({}),
  execute: async () => ({ todos: listTodos() })
});
const planSteps = createTool({
  id: "plan_steps",
  description: "Break a goal into an ordered checklist of steps on the board. Pass the goal's id and a short list of step descriptions.",
  inputSchema: z.object({ goalId: z.number(), steps: z.array(z.string()) }),
  execute: async ({ goalId, steps }) => ({ goalId, stepIds: steps.map((s) => addStep(goalId, s)) })
});
const completeTask = createTool({
  id: "complete_task",
  description: "Mark a todo (a step or the goal) with this id as done and record a short result summary.",
  inputSchema: z.object({ taskId: z.number(), result: z.string() }),
  execute: async ({ taskId, result }) => {
    completeTodo(taskId, result);
    return { taskId, status: "done" };
  }
});
const boardTools = { showTodos, planSteps, completeTask };
function makeFilesystem(dir = WORKSPACE) {
  return new MCPClient({
    servers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", dir],
        stderr: "ignore",
        cwd: dir
      }
    }
  });
}

mkdirSync(WORKSPACE, { recursive: true });
const provider = createOpenAI({
  baseURL: process.env.OLLAMA_API_BASE || "http://localhost:11434/v1",
  apiKey: "Ollama"
});
const model = provider("qwen2.5:7b");
const writerAgent = new Agent({
  id: "writer",
  name: "WriterAgent",
  instructions: "You are a professional creative marketer. Write a concise, 1-sentence product tagline. Do not use quotation marks.",
  model
});
const translatorAgent = new Agent({
  id: "translator",
  name: "TranslatorAgent",
  instructions: "You are an expert translator. Translate the given text exactly into natural Spanish. Return only the final Spanish text.",
  model
});
const writerStep = createStep({
  id: "writer",
  inputSchema: z.object({ task: z.string() }),
  outputSchema: z.object({ tagline: z.string() }),
  execute: async ({ inputData }) => {
    const result = await writerAgent.generate(inputData.task);
    return { tagline: result.text };
  }
});
const translatorStep = createStep({
  id: "translator",
  inputSchema: z.object({ tagline: z.string() }),
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData }) => {
    const result = await translatorAgent.generate(inputData.tagline);
    return { translation: result.text };
  }
});
const interrupterStep = createStep({
  id: "interrupter",
  inputSchema: z.object({ translation: z.string() }),
  resumeSchema: z.object({ shouldSave: z.boolean() }),
  suspendSchema: z.object({ translation: z.string() }),
  outputSchema: z.object({ translation: z.string(), shouldSave: z.boolean() }),
  execute: async ({ inputData, resumeData, suspend }) => {
    if (!resumeData) {
      console.log(`
\u{1F50D} [TRANSLATION PREVIEW]:
${inputData.translation}`);
      return await suspend({ translation: inputData.translation });
    }
    console.log(`\u{1F50D} DEBUG: shouldSave = ${resumeData.shouldSave}`);
    return { translation: inputData.translation, shouldSave: resumeData.shouldSave };
  }
});
const saverStep = createStep({
  id: "saver",
  inputSchema: z.object({ translation: z.string(), shouldSave: z.boolean() }),
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData, requestContext }) => {
    console.log("\n\u{1F527} [WORKFLOW INTEROP] Handing file operation over to MCP Filesystem...");
    const targetPath = join(WORKSPACE, "mastra_translate.txt");
    const filesystem = makeFilesystem();
    try {
      const tools = await filesystem.listTools();
      console.log("\u{1F50D} DEBUG available tools:", Object.keys(tools));
      const writeFile = tools["write_file"];
      if (!writeFile) {
        throw new Error(`write_file tool not found. Available: ${Object.keys(tools).join(", ")}`);
      }
      const execute = writeFile.execute;
      if (!execute) {
        throw new Error("write_file tool has no execute function");
      }
      const result = await execute(
        { path: targetPath, content: inputData.translation },
        { requestContext, observe: () => {
        } }
      );
      console.log("\u{1F50D} DEBUG tool result:", result);
      console.log(`\u2728 SUCCESS: MCP tool written to ${targetPath}`);
    } catch (e) {
      console.log(`\u26A0\uFE0F Direct MCP call failed (${e}). Falling back to manual write...`);
      await fs.writeFile(targetPath, inputData.translation, "utf-8");
      console.log(`\u2728 Fallback SUCCESS: File created at ${targetPath}`);
    } finally {
      await filesystem.disconnect();
    }
    return { translation: inputData.translation };
  }
});
const skipStep = createStep({
  id: "skip",
  inputSchema: z.object({ translation: z.string(), shouldSave: z.boolean() }),
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData }) => ({ translation: inputData.translation })
});
const formatterStep = createStep({
  id: "formatter",
  inputSchema: z.object({}).passthrough(),
  outputSchema: z.object({ formatted: z.string() }),
  execute: async ({ getStepResult }) => {
    const text = getStepResult(saverStep)?.translation ?? getStepResult(skipStep)?.translation ?? "";
    return { formatted: `*** BRAND OUTPUT ***
${text.toUpperCase()}` };
  }
});
const translationWorkflow = createWorkflow({
  id: "translation-workflow",
  inputSchema: z.object({ task: z.string() }),
  outputSchema: z.object({ formatted: z.string() })
}).then(writerStep).then(translatorStep).then(interrupterStep).branch([
  [async ({ inputData }) => inputData.shouldSave === true, saverStep],
  [async ({ inputData }) => inputData.shouldSave === false, skipStep]
]).then(formatterStep).commit();

const mastra = new Mastra({
  workflows: {
    translationWorkflow
  },
  storage: new LibSQLStore({
    id: "translation-workflow-storage",
    url: "file:./mastra.db"
  })
});
(async () => {
  try {
    const storage = mastra.getStorage();
    if (storage) {
      await storage.init();
      console.log("\u{1F4BE} [Mastra Dev Store] SQLite Storage initialized successfully!");
    }
  } catch (error) {
    console.error("\u26A0\uFE0F [Mastra Dev Store] Initialization crash:", error);
  }
})();

export { mastra };
