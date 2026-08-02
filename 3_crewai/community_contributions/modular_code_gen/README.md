# ModularCodeGen Crew

Welcome to the ModularCodeGen Crew project, powered by [crewAI](https://crewai.com).   

#  CrewAI – Modular Engineering Team (Agentic Version)

This project is an **agentic and modular transformation** of the original [engineering_team project](https://github.com/ed-donner/agents/tree/main/3_crew/engineering_team).  
Unlike the original monolithic implementation, this version introduces **fully separated backend modules**, each with its own **unit tests** and **automated frontend integration**, built using an orchestrated multi-agent workflow defined in `tasks.yaml`.

---

##  Overview

The **CrewAI** system automates the design, coding, testing, and integration of a Python backend and frontend architecture using specialized AI agents.  
All modules and their test files are stored under account_directory/.  
After running all tasks, the generated structure looks like:

account_directory/  
├── module_a.py  
├── test_module_a.py  
├── module_b.py  
├── test_module_b.py  
├── ...  
├── accounts.py          # main frontend API  
├── test_accounts.py     # frontend headless test  
└── README.md  


The main API can be launched with:

```bash
$ uv run python accounts.py
```

## Architecture Summary

This system decomposes the engineering workflow into **five coordinated tasks**, each handled by a specific agent role.  
All task definitions are provided in `tasks.yaml`.

---

### 1. `design_task`

- **Agent:** `engineering_lead`  
- **Goal:** Analyze given requirements and design a modular backend.  
- **Output:**  
  - List of module names (`module_names`)  
  - Specification of classes, methods, and interactions (`module_specs`)  
  - JSON schema describing the architecture  
- **Key Point:** Each module must have a **unique name**.

---

### 2. `code_task`

- **Agent:** `backend_engineer`  
- **Goal:** Implement Python code for each designed module.  
- **Output:**  
  - Source files (`module_sources`)  
  - Corresponding test files (`module_tests`)  
- **Test Framework:** `unittest`  
- **Constraint:**  
  - Outputs must be **pure Python code** (no markdown formatting).  
  - The number and names of modules must match the `design_task` exactly.  
  - Tests run in a **dedicated environment**.

---

### 3. `writer_task_back`

- **Agent:** `file_writer`  
- **Goal:** Persist all generated backend modules and tests to disk.  
- **Output Directory:** `account_directory/`
- **Output Files:**  
  - `{module_name}.py`  
  - `test_{module_name}.py`  
- **Also Generates:**  
  - A `README.md` describing each module and its functionality.  
- **Result:** All backend code is saved under `account_directory/` and ready for import.

---

### 4. `frontend_task`

- **Agent:** `frontend_engineer`  
- **Goal:** Build a lightweight Python API using gradio to expose endpoints for all backend modules.  
- **Outputs:**  
  - `fronted_source` – the frontend API source code.  
  - `fronted_test` – test verifying headless initialization of the API tool.  
- **Behavior:**  
  - The frontend automatically imports all backend modules.  
  - It runs in **headless mode** to confirm proper initialization.

---

### 5. `writer_task_front`

- **Agent:** `file_writer`  
- **Goal:** Persist frontend code and test files.  
- **Output Directory:** `account_directory/` 
- **Files Written:**  
  - `accounts.py`  
  - `test_accounts.py`  
- **Note:**  
  Before generating the frontend, the backend modules are **copied into the same directory** so the frontend can import and test them in headless mode.
