# Change Log

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