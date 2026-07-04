import "./env.ts";
import { join } from "node:path";
import { mkdirSync } from "node:fs";
import { createWorkflow, createStep } from "@mastra/core/workflows";
import { Agent } from "@mastra/core/agent";
import { createOpenAI } from "@ai-sdk/openai";
import { z } from "zod";
import * as fs from "fs/promises";
import * as readline from "readline/promises";
import { makeFilesystem, WORKSPACE } from "./tools.ts";
import { Mastra } from "@mastra/core";
import { LibSQLStore } from "@mastra/libsql";

mkdirSync(WORKSPACE, { recursive: true });

const provider = createOpenAI({
  baseURL: process.env.OLLAMA_API_BASE,
  apiKey: "Ollama",
});
const model = provider("qwen2.5:7b");

const writerAgent = new Agent({
  id: "writer",
  name: "WriterAgent",
  instructions: "You are a professional creative marketer. Write a concise, 1-sentence product tagline. Do not use quotation marks.",
  model,
});

const translatorAgent = new Agent({
  id: "translator",
  name: "TranslatorAgent",
  instructions: "You are an expert translator. Translate the given text exactly into natural Spanish. Return only the final Spanish text.",
  model,
});

const writerStep = createStep({
  id: "writer",
  inputSchema: z.object({ task: z.string() }),
  outputSchema: z.object({ tagline: z.string() }),
  execute: async ({ inputData }) => {
    const result = await writerAgent.generate(inputData.task);
    return { tagline: result.text };
  },
});

const translatorStep = createStep({
  id: "translator",
  inputSchema: z.object({ tagline: z.string() }),
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData }) => {
    const result = await translatorAgent.generate(inputData.tagline);
    return { translation: result.text };
  },
});

const interrupterStep = createStep({
  id: "interrupter",
  inputSchema: z.object({ translation: z.string() }),
  resumeSchema: z.object({ shouldSave: z.boolean() }),
  suspendSchema: z.object({ translation: z.string() }),
  outputSchema: z.object({ translation: z.string(), shouldSave: z.boolean() }),
  execute: async ({ inputData, resumeData, suspend }) => {
    if (!resumeData) {
      console.log(`\n🔍 [TRANSLATION PREVIEW]:\n${inputData.translation}`);
      return await suspend({ translation: inputData.translation });
    }
    console.log(`🔍 DEBUG: shouldSave = ${resumeData.shouldSave}`);
    return { translation: inputData.translation, shouldSave: resumeData.shouldSave };
  },
});

// FIX 1 + FIX 2: requestContext (not runtimeContext), and an explicit
// undefined check on the indexed tool before calling .execute()
const saverStep = createStep({
  id: "saver",
  inputSchema: z.object({ translation: z.string(), shouldSave: z.boolean() }),
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData, requestContext }) => {
    console.log("\n🔧 [WORKFLOW INTEROP] Handing file operation over to MCP Filesystem...");
    const targetPath = join(WORKSPACE, "mastra_translate.txt");
    const filesystem = makeFilesystem();

    try {
      const tools = await filesystem.listTools();
      console.log("🔍 DEBUG available tools:", Object.keys(tools));

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
        { requestContext, observe: () => {} } as any
      );

      console.log("🔍 DEBUG tool result:", result);
      console.log(`✨ SUCCESS: MCP tool written to ${targetPath}`);
    } catch (e) {
      console.log(`⚠️ Direct MCP call failed (${e}). Falling back to manual write...`);
      await fs.writeFile(targetPath, inputData.translation, "utf-8");
      console.log(`✨ Fallback SUCCESS: File created at ${targetPath}`);
    } finally {
      await filesystem.disconnect();
    }

    return { translation: inputData.translation };
  },
});

const skipStep = createStep({
  id: "skip",
  inputSchema: z.object({ translation: z.string(), shouldSave: z.boolean() }),
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData }) => ({ translation: inputData.translation }),
});

// FIX 3: pass the step objects themselves to getStepResult(), not string
// IDs, so TypeScript can infer the shape from each step's outputSchema
const formatterStep = createStep({
  id: "formatter",
  inputSchema: z.object({}).passthrough(),
  outputSchema: z.object({ formatted: z.string() }),
  execute: async ({ getStepResult }) => {
    const text = getStepResult(saverStep)?.translation ?? getStepResult(skipStep)?.translation ?? "";
    return { formatted: `*** BRAND OUTPUT ***\n${text.toUpperCase()}` };
  },
});

export const translationWorkflow = createWorkflow({
  id: "translation-workflow",
  inputSchema: z.object({ task: z.string() }),
  outputSchema: z.object({ formatted: z.string() }),
})
  .then(writerStep)
  .then(translatorStep)
  .then(interrupterStep)
  .branch([
    [async ({ inputData }) => inputData.shouldSave === true, saverStep],
    [async ({ inputData }) => inputData.shouldSave === false, skipStep],
  ])
  .then(formatterStep)
  .commit();


const mastra = new Mastra({
  workflows: { translationWorkflow },
  storage: new LibSQLStore({
    id: "translation-workflow-storage",
    url: "file:./mastra.db",
  }),
});

console.log("cwd:", process.cwd());
console.log("storage attached:", !!mastra.getStorage());
await mastra.getStorage()?.init();
console.log("storage init attempted");

async function main() {
  console.log("🎬 Starting Mastra Translation Workflow...");

  const workflow = mastra.getWorkflow("translationWorkflow");
  const run = await workflow.createRun();

  let result = await run.start({
    inputData: { task: "A high-performance organic energy drink for programmers." },
  });

  if (result.status === "suspended") {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const answer = (await rl.question("💾 Would you like to save this translation to a file? (y/n): "))
      .trim()
      .toLowerCase();
    rl.close();

    result = await run.resume({
      step: "interrupter",
      resumeData: { shouldSave: answer === "y" || answer === "yes" },
    });
  }

  console.log("\n🏁 [WORKFLOW EXECUTION COMPLETE]");
  if (result.status === "success") {
    const output = result.result as { formatted: string };
    console.log(output.formatted);
  } else {
    console.log(result);
  }

  process.exit(0);
}

main();