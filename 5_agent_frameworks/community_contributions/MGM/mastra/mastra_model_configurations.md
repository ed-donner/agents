# Mastra Models Configurations
To provide parameters and model configurations in Mastra, you can configure them at two levels: globally inside the Agent definition (for all calls made by that agent) or locally inside the step execution (dynamically per run).

## 1. Global Agent Configuration
You can pass model parameters directly into the Agent constructor using the options property. This includes configuration parameters like temperature, maxTokens, topP, and presencePenalty. [1] 
```ts
const writerAgent = new Agent({
  id: "writer",
  name: "WriterAgent",
  instructions: "You are a professional creative marketer...",
  model,
  // Pass model-specific parameters here:
  options: {
    temperature: 0.7,      // Controls randomness (0 = deterministic, 1 = creative)
    maxTokens: 100,        // Caps the length of the generation
    topP: 0.9,             // Nucleus sampling threshold
    presencePenalty: 0.5,  // Penalizes repeated topics
  }
});
```
## 2. Runtime Step Configuration
If you want a single agent to use different parameters depending on the specific workflow step, you can pass an options object as the second argument to agent.generate().
```ts
const writerStep = createStep({
  id: "writer",
  inputSchema: z.object({ task: z.string() }),
  outputSchema: z.object({ tagline: z.string() }),
  execute: async ({ inputData }) => {
    // Override settings dynamically during workflow execution
    const result = await writerAgent.generate(inputData.task, {
      temperature: 0.3,    // Make this specific step more precise
      maxTokens: 50,
    });
    return { tagline: result.text };
  },
});
```
## 3. Workflow Global Inputs
If your parameters need to be controlled by the user starting the workflow (e.g., letting the user pick a temperature), add them to your workflow's inputSchema and pass them down the chain.
```ts
// Update your workflow schema to accept runtime parameters
export const translationWorkflow = createWorkflow({
  id: "translation-workflow",
  inputSchema: z.object({ 
    task: z.string(),
    creativity: z.number().min(0).max(1).default(0.7) // User-defined param
  }),
  outputSchema: z.object({ formatted: z.string() }),
})
  .then(writerStep)
  // ... rest of your workflow
```
Then consume it in your step via the pipeline data:
```ts
const writerStep = createStep({
  id: "writer",
  inputSchema: z.object({ task: z.string(), creativity: z.number() }),
  outputSchema: z.object({ tagline: z.string() }),
  execute: async ({ inputData }) => {
    const result = await writerAgent.generate(inputData.task, {
      temperature: inputData.creativity, // Using the parameter from workflow input
    });
    return { tagline: result.text };
  },
});
```

## Structured Output Schema
To get structured outputs from your Mastra agents, you pass a Zod schema into the outputSchema property of the agent.generate() options object. This forces the underlying LLM to return valid JSON matching your schema structure. [2] 

### 1. Update the Agent Execution to return Structured JSON
Modify your writerStep to pass an outputSchema to writerAgent.generate(). Mastra parses the result automatically, changing result.text into a fully typed result.object.
```ts
// Define your structured output schema
const taglineSchema = z.object({
  tagline: z.string().describe("The primary catchy 1-sentence slogan"),
  keywords: z.array(z.string()).describe("3-4 SEO or brand keywords associated with the tagline"),
  toneAnalysis: z.string().describe("A brief explanation of why this fits the marketing vibe")
});

const writerStep = createStep({
  id: "writer",
  inputSchema: z.object({ task: z.string() }),
  // Update step output schema to match the new structure
  outputSchema: taglineSchema, 
  execute: async ({ inputData }) => {
    // Pass the outputSchema option directly here
    const result = await writerAgent.generate(inputData.task, {
      outputSchema: taglineSchema,
    });

    // result.object is now strongly typed based on your Zod schema
    return {
      tagline: result.object.tagline,
      keywords: result.object.keywords,
      toneAnalysis: result.object.toneAnalysis,
    };
  },
});
```
### 2. Update the downstream steps to support the new JSON structure
Because your writerStep now produces an object with multiple properties rather than just a string, ensure that your translatorStep accesses the specific property it needs:
```ts
const translatorStep = createStep({
  id: "translator",
  // Expect the structured object from the writer step
  inputSchema: taglineSchema, 
  outputSchema: z.object({ translation: z.string() }),
  execute: async ({ inputData }) => {
    // Only pass the tagline string field to the translator agent
    const result = await translatorAgent.generate(inputData.tagline);
    return { translation: result.text };
  },
});
```
### Pro Tip for Prompts
When using outputSchema, it is best practice to keep your instructions focused on the content and quality. Let the describe() methods inside your Zod schema guide the model on formatting, as Mastra uses them to generate the system constraint JSON schemas behind the scenes. [3] 

[1] [https://www.getopenclaw.ai](https://www.getopenclaw.ai/how-to/openclaw-configuration-guide)
[2] [https://lunary.ai](https://lunary.ai/structured-output-schema-generator)
[3] [https://techsy.io](https://techsy.io/en/blog/llm-structured-outputs-guide)
