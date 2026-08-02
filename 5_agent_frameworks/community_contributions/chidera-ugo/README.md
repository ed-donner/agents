# Interview Prep Swarm

A week 5 AutoGen assessment project. A swarm of AI interviewers — each with a different background and speciality — generates and cross-refines interview questions for a target role.

## How it works

1. `world.py` spins up a gRPC distributed runtime and sends 10 parallel requests to a `Creator` agent
2. `Creator` reads `agent.py` as a template and generates a unique interviewer persona for each request (FAANG engineer, startup CTO, accessibility specialist, TDD advocate, etc.)
3. Each interviewer generates 8 targeted questions for the job role (4 technical, 2 behavioural, 2 situational)
4. Each interviewer has a 50% chance of passing their questions to a peer for refinement — harder follow-ups get added, weak questions get cut
5. Results are saved to `output/questions1.md` through `output/questions10.md`

## Usage

### 1. Configure the role

Edit `world.py` and update `JOB_ROLE` with the job description you're preparing for:

```python
JOB_ROLE = """
Senior Frontend Engineer at a fintech scale-up.
...
"""
```

### 2. Install dependencies

```bash
pip install autogen-agentchat autogen-ext[grpc,openai] python-dotenv
```

### 3. Add your API key

```env
# .env
OPENAI_API_KEY=your_key_here
```

### 4. Run

```bash
python world.py
```

Results appear in `output/`.

## What you get

10 markdown files, each from a different interviewer perspective. Because agents refine each other's questions at random, some files will contain question sets that have been sharpened by multiple interviewers. Read across all 10 to build a comprehensive prep bank.

## Customisation

| What | Where |
|---|---|
| Change the target role | `JOB_ROLE` in `world.py` |
| More or fewer interviewers | `HOW_MANY_AGENTS` in `world.py` |
| Change how often agents collaborate | `CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER` in `agent.py` |
| Change the base interviewer persona | `system_message` in `agent.py` |
