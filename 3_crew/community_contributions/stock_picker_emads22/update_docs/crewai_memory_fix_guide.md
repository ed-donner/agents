# CrewAI Memory Configuration Fix (October 2025)

## 1. What Caused the Issue

The error occurred because we were **manually instantiating** `ShortTermMemory`, `LongTermMemory`, and `EntityMemory` and passing them directly to the `Crew()` constructor.
This approach is **not supported** with the current basic memory system.

CrewAI has since moved to a **simplified memory configuration** using a single flag:

```python
memory=True
```

Additionally, when using OpenAI embeddings with ChromaDB, the environment variable
`CHROMA_OPENAI_API_KEY` is **required** for the embedding function to work properly.

**Reference:** [Official CrewAI Memory Documentation](https://docs.crewai.com/en/concepts/memory)

---

## 2. How to Fix It

### Step 1: Remove Manual Memory Instantiation

CrewAI automatically sets up all memory types when `memory=True` is used.
There’s no need to create `ShortTermMemory`, `LongTermMemory`, or `EntityMemory` manually.

---

### Step 2: Enable Memory in `Crew()`

Pass `memory=True` in the `Crew()` constructor.
This activates **short-term** (RAG), **long-term** (SQLite), and **entity memory** automatically.

```python
return Crew(
    agents=self.agents,
    tasks=self.tasks,
    process=Process.hierarchical,
    verbose=True,
    manager_agent=manager,
    memory=True
)
```

---

### Step 3: Use `embedder` for Embedding Configuration

Instead of configuring embeddings through `RAGStorage`, pass an `embedder` dictionary to `Crew()`:

```python
embedder={
    "provider": "openai",
    "config": {"model": "text-embedding-3-small"}
}
```

This is the officially supported way to set embedding models for CrewAI memory.

---

### Step 4: Set `CHROMA_OPENAI_API_KEY`

Even when using local ChromaDB, Chroma’s embedding function checks for
`CHROMA_OPENAI_API_KEY` rather than `OPENAI_API_KEY`.

To fix this:

```python
import os
if "OPENAI_API_KEY" in os.environ:
    os.environ["CHROMA_OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
```

---

### Step 5: Optional – Set a Custom Storage Directory

By default, CrewAI stores memory in OS-specific directories.
To keep it inside our project (`os.path.abspath()` ensures the memory directory is created exactly inside the
project folder, not in AppData):

```python
os.environ["CREWAI_STORAGE_DIR"] = os.path.abspath("./memory")
```

This makes it easier to inspect or version-control our memory files.

---

## 3. Final Working Example

```python
import os
from crewai import Crew, Process

@crew
def crew(self) -> Crew:
    # Ensure Chroma can find the OpenAI key
    if "OPENAI_API_KEY" in os.environ:
        os.environ.setdefault("CHROMA_OPENAI_API_KEY", os.environ["OPENAI_API_KEY"])

    # Optional: set storage dir relative to project
    os.environ.setdefault("CREWAI_STORAGE_DIR", "./memory")

    # Manager agent orchestrates the flow in hierarchical process mode
    manager = Agent(
        config=self.agents_config["manager"],
        allow_delegation=True,
    )

    # Defines the crew with all agents, tasks, and manager
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.hierarchical,
        verbose=True,
        manager_agent=manager,
        memory=True,
        embedder={
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"}
        }
    )
```

---

## 4. How CrewAI Handles Memory Internally

| Memory Type       | Backend         | Managed Automatically | Triggered By  |
| ----------------- | --------------- | --------------------- | ------------- |
| Short-Term Memory | ChromaDB (RAG)  | ✅ Yes                 | `memory=True` |
| Long-Term Memory  | SQLite Database | ✅ Yes                 | `memory=True` |
| Entity Memory     | ChromaDB (RAG)  | ✅ Yes                 | `memory=True` |

CrewAI **routes memory automatically** when `memory=True` is set.
There’s no need to instantiate or label memory components manually.

---

## 5. Summary

* ❌ Manual instantiation of memory objects is no longer needed.
* ✅ `memory=True` automatically sets up short-term, long-term, and entity memory.
* 🧠 Use `embedder` for embeddings configuration.
* 🔐 Ensure `CHROMA_OPENAI_API_KEY` is set (required for OpenAI embeddings with Chroma).
* 🗂️ Optional: set `CREWAI_STORAGE_DIR` to store memory inside our project.

---