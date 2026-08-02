# ✅ Workaround for MCP in Autogen Lab 2 on Windows

Running MCP-based tools in **Jupyter Notebook** on Windows often causes this error:

```

UnsupportedOperation: fileno

````

This is due to limitations in how subprocesses and `fileno()` work inside notebook environments on Windows.

---

## 🛠️ Workaround: Run MCP in a `.py` script

Follow these steps to run your MCP tool using a standalone script instead of a notebook:

---

### 1️⃣ Start the MCP Server (in a separate terminal)

Run the following command **in a new terminal**:

```bash
uvx mcp-server-fetch
````

This launches the MCP server in stdio mode (no need for extra flags). Keep this terminal open.

---

### 2️⃣ Run the Python Script (in another terminal)

In a second terminal, run the MCP script using:

```bash
uv run mcp_fetch.py
```

> You can also use `python mcp_fetch.py` if you've already activated your virtual environment.

---

### ✅ Expected Output (Example)

```markdown
# Summary of edwarddonner.com

- Edward Donner is a software engineer...
- Co-founder of Nebula.io...
- Offers AI-related events and workshops...

TERMINATE
```

---

### 💡 Notes

* You **must** start the MCP server before running the Python script.
* This workaround avoids subprocess issues that commonly occur in Windows Jupyter environments.

---
