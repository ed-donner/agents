# Week 3 Exercise - AI Debate System with Different LLMs

**Contributor:** Akhila Guska ([@akhilaguska27](https://github.com/akhilaguska27))
**Course:** AI Engineer Agentic Track - The Complete Agent & MCP Course

## What This Contribution Does

Extends the original debate crew by splitting the single debater agent into
two separate agents - one for proposing and one for opposing - each using
a different LLM model. This allows you to battle different AI models against
each other in a debate and see which is more persuasive.

## Changes from Original

Original design:
- One debater agent used for both propose and oppose tasks
- Single model for all agents

This contribution:
- proposer agent (gpt-4o-mini) argues FOR the motion
- opposer agent (gpt-4o) argues AGAINST the motion
- judge agent (gpt-4o-mini) picks the winner

## How to Run

Navigate to the debate folder and run:

    cd 3_crew/debate
    crewai run

## How to Experiment

Change the llm field in agents.yaml to battle different models:
- openai/gpt-4o-mini vs openai/gpt-4o
- openai/gpt-4o vs anthropic/claude-3-7-sonnet-latest
- Switch proposer and opposer models to see if outcome changes

## Result

gpt-4o-mini (FOR regulation) beat gpt-4o (AGAINST regulation).
The judge may favor arguments from its own model family - try swapping to test!
