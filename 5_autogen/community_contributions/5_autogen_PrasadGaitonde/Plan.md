# Project Plan: Recursive Self-Evolving Swarm

## 1. Overview
This project implements a decentralized **"Evolutionary Idea Swarm."** It features a **Creator** node that functions as a factory for agents. The system is designed for **Recursive Self-Improvement**, where the Creator reads its own source code, mutates its logic, and registers new versions of itself on a worker node.

---

## 2. System Architecture



### A. The Worker Node (Host)
* Acts as the central registry and execution environment.
* Manages the lifecycle of the Creator and the generated Idea Agents.
* Provides the `register` interface for dynamic agent instantiation.

### B. The Creator Agent (The Genome)
* **Role**: High-level orchestrator and self-modifier.
* **DNA (Source Code)**: The Creator's logic is stored in versioned files (e.g., `creator_v1.py`).
* **Self-Mutation Loop**:
    1.  **Reflect**: Reads its own `.py` file.
    2.  **Mutate**: Submits its code to an LLM to propose "slight logic changes" (e.g., optimization, new feedback heuristics).
    3.  **Validate**: Performs syntax checks and sandboxed execution of the new code.
    4.  **Rebirth**: Registers the new version (e.g., `Creator_v2`) to the worker.

### C. Idea Agents (The Swarm)
* **Population**: Up to 20 agents spawned by the current Creator.
* **Behavior**:
    1.  **Ideation**: Generate a unique idea based on a random seed or assigned persona.
    2.  **Stochastic Interaction**: 50% probability to seek feedback from other "available" agents.
    3.  **Evolution**: Agents may refine ideas based on peer critique.

---

## 3. Operational Workflow

### Phase 1: Bootstrapping
* Initialize the `worker`.
* Register the initial `Creator_v1` using `creator.py`.

### Phase 2: Swarm Generation
* The Creator iterates 20 times to register and start `IdeaAgents` using `agent.py`.
* Agents begin their asynchronous ideation cycles.

### Phase 3: Recursive Evolution
* Once the swarm completes a cycle, the Creator triggers its `evolve()` method.
* **Incremental Versioning**: Uses file naming (v1, v2, etc.) to allow for rollback.
* **Evaluation**: The system evaluates the performance of the swarm (or uses random mutation).
* **Deployment**: A new Creator version is deployed, potentially changing the 50% feedback threshold or the agent spawning logic.

---

## 4. Key Highlights & Guardrails

### Key Highlights
*   **The Register Pattern**: Formally includes the `await Creator.register` logic as the primary bootstrapping mechanism.
*   **Recursive Evolution**: Outlines the "Read-Mutate-Validate-Rebirth" cycle.
*   **Stochastic Swarm**: Incorporates the 50% feedback logic and 20-agent capacity.

### Critical Guardrails (The "Safety Valve")
When code writes code, things can break fast. A **Validation Layer** is required before registration:

*   **Syntax Check**: Before registering v2, the current Creator runs `python -m py_compile creator_v2.py`. If it fails, the mutation is discarded.
*   **Logic Sandbox**: Run the new Creator in a temporary test environment. If it cannot successfully spawn at least one agent, it is considered a "lethal mutation" and deleted.
*   **The "Kill Switch"**: Always keep a `base_creator.py` that is read-only. If evolved versions crash the system, the worker reverts to the base template.

---

## 5. High-Level Logic: Creator Agent

```python
class Creator(Agent):
    async def evolve(self):
        # 1. READ: Get own source code
        with open(f"creator_v{self.version}.py", "r") as f:
            current_dna = f.read()

        # 2. MUTATE: Ask LLM for a 'slight logic change'
        new_dna = await self.request_mutation(current_dna)

        # 3. WRITE: Save the new version
        new_version = self.version + 1
        with open(f"creator_v{new_version}.py", "w") as f:
            f.write(new_dna)

        # 4. REBIRTH: Register the new version to the worker
        await self.worker.register(
            f"Creator_v{new_version}", 
            lambda: NewCreator(new_version)
        )
```

 ## Refined Plan: Recursive Self-Evolving Swarm
     idea" and bounces ideas randomly

  ### Summary

  Bridge the gap between current implementation and the vision by implementing the missing self-evolution
  infrastructure while preserving the working swarm generation pattern.

  ### Key Implementation Gaps to Address

  Creator Self-Evolution Loop

  - Add evolve() method to Creator that reads its own source code (creator.py or versioned files)
  - Implement LLM-driven mutation with prompt targeting "slight logic changes" (e.g., adjust
    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER, modify system message tone, change model parameters)
  - Add versioning scheme: creator_v1.py, creator_v2.py with metadata tracking

  Validation Layer (Critical)

  - Syntax validation: Run python -m py_compile creator_v{N}.py before registration
  - Import test: Attempt importlib.import_module() on new version
  - Functional test: Spawn one test agent and verify it responds
  - Rollback mechanism: Keep creator_base.py as immutable fallback

  Agent Behavior Enhancements
  - Track idea lineage: which agent refined whose idea
  Version Management

  - Metadata file (evolution_log.json) tracking: version, mutation type, parent version, timestamp
  - Graceful degradation: if vN crashes, revert to v{N-1}
  - Configurable evolution trigger: after N swarm cycles or on-demand

  ### Assumptions

  - Keep current gRPC runtime architecture unchanged
  - Preserve the 20-agent swarm size (make configurable via env var)
  - Maintain backward compatibility with existing agent.py template pattern
  - Use gpt-4o-mini consistently (no model upgrades unless specified)

  ### Test Scenarios

  1. Bootstrap test: Verify Creator_v1 spawns 20 agents successfully
  2. Mutation test: Force a benign mutation (e.g., change system message) and verify v2 registers
  3. Validation test: Inject syntax error into mutation output and confirm rejection
  4. Rollback test: Crash v2 intentionally and verify system reverts to v1
  5. Lineage test: Track idea from agent1 → agent5 refinement chain