#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from ghost_writer.crew import GhostWriter

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    
    idea = """Write a deeply philosophical and emotionally resonant novel in the spirit of Zen and the Art of 
    Motorcycle Maintenance, but from the perspective of a profoundly intelligent earthworm who perceives the world 
    solely through the sense of touch.
    
    The worm—C. Lumbricus, a subterranean philosopher and soil cartographer—lives in the shadowy labyrinth beneath 
    the surface, where all knowledge is felt, not seen. He cannot see color, light, or form. His understanding of 
    the world is shaped entirely through pressure, texture, vibration, and weight. Each pebble is a poem. Each 
    root is a question. Each rainfall is a moral dilemma.Over the course of the novel, C. Lumbricus embarks on a 
    symbolic and literal journey through layers of soil, compost heaps, human-tilled gardens, and the strange 
    violence of the surface world. As he tunnels, he reflects on the nature of self, consciousness, purpose, and 
    impermanence, interpreting the subtle shifts in the earth like a blind monk reading scripture in Braille.

    Themes to explore include:
    - Identity without appearance: What does it mean to be when you cannot see yourself?
    - Epistemology of pressure: How can truth be known through touch alone?
    - Technology and interference: How do the mechanical intrusions of humans (shovels, tillers, pipes) disrupt 
      the ancient wisdom of the earth?
    - Dualism and wholeness: Through his regeneration after injury, C. Lumbricus contemplates the split between 
      body and being.
    - Love and resonance: The worm encounters another being whose vibrational pattern harmonizes with his own, and 
      together they explore tactile connection beyond utility.

    The tone is meditative, poetic, and layered with metaphor. The worm’s limitations shape the form of the prose 
    itself—imagery becomes metaphor made tactile. Light is never described. Instead, insight is a loosening of 
    compacted clay. Despair is the collapse of a burrow. Revelation is the warm pressure of composted moss.

    Let the novel not simply be about a worm, but about what it means to know, to feel meaning in a dark, 
    indifferent world, and to press forward—segment by segment—in search of coherence, even when no eyes will ever 
    see the map you leave behind."""

    inputs = {
        'idea': idea,
        'author': 'Morgan Vale',
        'title': 'Tactile Reveries: Meditations on Absence and Presence'
    }
    
    try:
        GhostWriter().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
