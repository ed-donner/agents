/**
 * Register the worker agent so Mastra's Studio can show it.
 *
 * `npm run dev` (mastra dev) reads this file, finds the Mastra instance, and opens
 * Studio at http://localhost:4111, a local UI where you chat with the agent and watch
 * every model step, tool call and result render live. We seed one goal here, an English
 * note to translate, so there is something on the board when Studio opens; ask the
 * worker to work the goal and it reads the note, translates it, records the Spanish on
 * the board, and replies with it.
 *
 * This agent gets the board tools only, not the filesystem MCP. Studio bundles the app
 * and runs it from .mastra/output, where a spawned `npx` is not on PATH, so the MCP
 * server cannot start here ("spawn npx ENOENT"). So the Studio goal carries its text on
 * the board itself; the full file worker with the filesystem MCP runs from the terminal
 * as worker.ts (npm run worker).
 */

import "../../env.ts";
import { translationWorkflow } from "../../workflow.ts";
import { Mastra } from "@mastra/core";
import { LibSQLStore } from "@mastra/libsql";

// 1. Initialize and configure your Mastra app instance for the dev server
export const mastra = new Mastra({
  workflows: { 
    translationWorkflow 
  },
  storage: new LibSQLStore({
    id: "translation-workflow-storage",
    url: "file:./mastra.db",
  }),
});

// 2. Automatically trigger storage migrations when Mastra dev environments stand up
// Using an un-awaited block lets the Dev UI hook up quickly without freezing
(async () => {
  try {
    const storage = mastra.getStorage();
    if (storage) {
      await storage.init();
      console.log("💾 [Mastra Dev Store] SQLite Storage initialized successfully!");
    }
  } catch (error) {
    console.error("⚠️ [Mastra Dev Store] Initialization crash:", error);
  }
})();
