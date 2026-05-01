from mcp.server.fastmcp import FastMCP
import random

mcp = FastMCP("Coping Server")

def get_strategies(emotion: str):
    emotion = emotion.lower()

    strategies = {
        "anxiety": [
            {
                "title": "4-4-4 Breathing",
                "how": "Inhale 4 sec → hold 4 → exhale 4. Repeat 5 times.",
                "why": "Helps regulate the nervous system"
            },
            {
                "title": "Grounding (5-4-3-2-1)",
                "how": "Name 5 things you see, 4 feel, 3 hear, 2 smell, 1 taste.",
                "why": "Brings attention back to the present"
            },
            {
                "title": "Cold Water Reset",
                "how": "Splash cold water on your face or hold something cold.",
                "why": "Activates vagus nerve and reduces stress"
            }
        ],
        "stress": [
            {
                "title": "Micro-break",
                "how": "Step away for 2 minutes and stretch your body.",
                "why": "Reduces cortisol buildup"
            },
            {
                "title": "Task Dump",
                "how": "Write everything on your mind in 1 minute.",
                "why": "Clears cognitive overload"
            }
        ],
        "sad": [
            {
                "title": "Light Movement",
                "how": "Take a slow 5–10 min walk.",
                "why": "Boosts serotonin gently"
            },
            {
                "title": "Reach Out",
                "how": "Message or call someone you trust.",
                "why": "Social connection reduces emotional load"
            }
        ],
        "low": [
            {
                "title": "Sunlight Exposure",
                "how": "Sit near sunlight or step outside for 5–10 min.",
                "why": "Supports circadian rhythm and mood"
            }
        ]
    }

    
    default = [
        {
            "title": "Pause & Breathe",
            "how": "Take 5 slow breaths.",
            "why": "Helps reset your system"
        }
    ]

    
    for key in strategies:
        if key in emotion:
            return random.sample(strategies[key], min(3, len(strategies[key])))

    return default


@mcp.tool()
def get_coping_methods(emotion: str):
    """
    Return emotion-specific coping strategies with explanation.
    """

    results = get_strategies(emotion)

    formatted = []

    for s in results:
        formatted.append(
            f"{s['title']}: {s['how']} ({s['why']})"
        )

    return formatted


if __name__ == "__main__":
    mcp.run()