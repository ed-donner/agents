/**
 * Step 4: Add MCP.
 *
 * MCP is just more tools: ones you did not write, connected over a small protocol.
 * We give the agent the filesystem reference server, the same Node server every
 * framework uses this week, scoped to a single workspace folder. In Mastra an MCP
 * server is an MCPClient; you pull its tools with await mcp.listTools() and hand
 * them to the agent. makeFilesystem (in tools.ts) sets stderr "ignore" and cwd on
 * the server, the clean way Mastra handles the banner and path wrinkles. Run it
 * with: npm run step4
 */

import "./env.ts";
import { Agent } from "@mastra/core/agent";
import { makeFilesystem } from "./tools.ts";

const filesystem = makeFilesystem();

const fileAgent = new Agent({
  id: "file-agent",
  name: "File Agent",
  instructions: "You can read and write files in your workspace. Use your tools to do what is asked.",
  model: "openai/gpt-5.4-mini",
  tools: await filesystem.listTools(),
});

const reply = await fileAgent.generate("Read notes.txt and summarize it in one short sentence.");
console.log(reply.text);

await filesystem.disconnect();

process.exit(0); // Mastra keeps its model connection pool open, so exit once the work is done
