# Change Log

## **Week 6: Run Agentic Stock Trader using MCP**


### **Updates**
* **Replaced Brave with Tavily Search:** It was required to add a plan and a credit card to get the API, the Tremendous card does not pass validation. 
* **Using Openrouter as default model** My credit in OpenAI is almost gone.
* **Monitoring Traces** With OpenAI SDK

###  **Next Steps**
* **Evaluate responses:** Create a Pydantic model for the Evaluation and generate metrics to assess the model performance.


## **Week 4: Improve LangGraph Sidekick**
Focused on upgrading the agent's core capabilities for independent development, moving from general search to LLM-optimized retrieval.

### **Updates**
* **Replaced Serper with Tavily Search:** Switched to an AI-native search engine to provide cleaner, structured content better suited for LLM context windows.
* **Added YouTube Search Tool:** Integrated a new tool to allow the agent to retrieve video-based tutorials and lectures for the Course Notes Handbook.
* **Integrated LangSmith Tracing:** Configured environment variables (`LANGCHAIN_TRACING_V2`) and project tracking to monitor agent reasoning, latency, and costs in real-time.

### **Dependencies Added/Updated**
* `tavily-python`
* `Youtube`
* `langsmith`

### **Next Steps**
* **Implement "Human-in-the-Loop":** Add a pause/interrupt node in LangGraph to allow for manual approval before the agent executes critical actions.
* **Use Corrective RAG (CRAG):** Build a loop that evaluates the quality of retrieved documents and triggers a re-search if the information is irrelevant.
* **Explore MCP (Model Context Protocol):** Investigate setting up an MCP server to connect the agent directly to local files and IDE data.


## Week2:  SDR implementation
This code implements an automated sales development representative (SDR) system which involves creating and enhancing skills 
with agentic workflows by employing learnings from the previous week, such as structured outputs and custom tools.

1. **Generates cold emails** using three different AI agents (DeepSeek, Gemini, Llama) with distinct writing styles (professional, humorous, concise)
2. **Selects the best draft** via a Sales Manager agent that evaluates and picks the most effective email
3. **Formats and sends the email** through an Email Manager that adds a subject, converts to HTML, and sends via Gmail SMTP
4. **Tracks the entire process** using OpenAI's tracing systemfor monitoring and debugging

The workflow: Sales Manager → generates 3 drafts → selects best → Email Manager → sends email.

### Next Steps
- Add more input and output **guardrails**.
- Use **structured outputs** for the email generation.
- **Evaluate responses:** Create a Pydantic model for the Evaluation and generate metrics to assess the model performance.


## Week 1: Carrer Agent with RAG
Build over the course Career Agent shown in Day 4 using Retrieval Augmented Generation to answer specific questions not available in Linkedin.

- **ChromaDB Integration:** Set up persistent vector storage for extracted data.
- **Extract properties from Markdown sections:** To minimize files commited I extracted the summary property from a private Markdown file using a new function.
- **Context Retrieval:** Added logic to augment LLM prompts with retrieved documents. These are loaded before the UI runs.

### Dependencies Added:
- chromadb
- glob

### Next Steps
- **Evaluate responses:** Create a Pydantic model for the Evaluation and generate metrics to assess the model performance.