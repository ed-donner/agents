---
name: northwind-slide
description: House style for Northwind Advisory one-slide fleet recommendation decks. Use whenever a fleet recommendation needs to be turned into a PowerPoint slide.
---

# Northwind Advisory recommendation slide

## When to use

Use this skill when a briefing ends with a recommendation and someone asks for a slide. Create one slide, not a full deck.

## House style

- State the chosen vehicle in the title, such as "Recommended: Tesla Model Y". Keep it under 40 characters
- Give exactly three key points. Start each with a one-word label and a colon, such as "Range: 330 real-world miles"
- Write one plain sentence that names the choice and its strongest reason
- Focus on the words. `create_slide` applies the colours, layout, and footer

## Workflow

1. Read the briefing or comparison
2. Choose three key points and one recommendation sentence
3. Call `create_slide` with the title, key points, and recommendation
