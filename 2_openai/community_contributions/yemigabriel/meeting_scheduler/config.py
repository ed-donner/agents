from dotenv import load_dotenv

load_dotenv(override=True)

WORKDAY_START = 9
WORKDAY_END = 17
DEFAULT_TIMEZONE = "Africa/Lagos"

EXAMPLE_REQUESTS = [
    "Schedule a 30-minute Q2 launch planning meeting for alice@example.com, bob@example.com, carol@example.com, and yemigabriel@gmail.com on 2026-03-31. Preferences: morning if possible, avoid lunch, earliest slot. Yes, please send the calendar invites to everyone once the meeting is confirmed.",
    "Book a 60-minute architecture review for alice@example.com, dave@example.com, and yemigabriel@gmail.com on 2026-03-31. Preference: afternoon. Please go ahead and send invites after scheduling.",
]
