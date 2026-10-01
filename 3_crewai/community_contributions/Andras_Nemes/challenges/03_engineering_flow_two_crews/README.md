# Engineering Flow with Two Crews

This challenge introduces a CrewAI Flow that coordinates two small crews:

The project uses `contract-first` parallel work.

- BackendCrew implements a Python backend from a requirement and contract.
- TestCrew independently writes tests from the same contract.
- EngineeringFlow starts both crews in parallel, waits for both, then runs the
  tests inside Docker.

See [FLOW_OVERVIEW.md](FLOW_OVERVIEW.md) for a beginner-friendly explanation.

## Run it

From this folder:

```powershell
crewai install
crewai run
```

Results are written to output/backend.py, output/test_backend.py, and
output/test_results.txt.
