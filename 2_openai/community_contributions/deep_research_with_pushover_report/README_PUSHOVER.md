# Deep Research with Pushover Notifications

This folder contains an alternative implementation of the deep research system that uses Pushover notifications instead of email notifications.

## Files

- **New Pushover files**:
  - `pushover_notification_agent.py` - Notification agent using Pushover
  - `pushover_research_manager.py` - Research manager using Pushover
  - `deep_research_pushover.py` - Gradio web interface with Pushover
  - `launch_pushover_ui.py` - Quick launcher with setup validation

## Setup

1. **Install Pushover app** on your device from:
   - iOS: App Store
   - Android: Google Play Store
   - Desktop: https://pushover.net/clients

2. **Get your Pushover credentials**:
   - Create account at https://pushover.net/
   - Create a new application at https://pushover.net/apps/build
   - Note your "API Token/Key" and "User Key"

3. **Replace .env.example with your .env file**:
   ```
   PUSHOVER_TOKEN=your_app_token_here
   PUSHOVER_USER=your_user_key_here
   ...
   ```

## Usage

### Option 1: Quick Launch (Recommended)
```bash
cd /path/to/deep_research
python launch_pushover_ui.py  
#if you're using UV, you can use `uv run launch_pushover_ui.py`
```
This will validate your setup and launch the web interface automatically.

### Option 2: Direct Launch
```bash
cd /path/to/deep_research
python deep_research_pushover.py
#if you're using UV, you can use `uv run deep_research_pushover.py`
```

### Option 3: Import the notification agent
```python
from pushover_notification_agent import notification_agent
from agents import Runner

# Send a notification
result = await Runner.run(notification_agent, "Your research report content here")
```

## Web Interface Features

🌐 **Gradio Web Interface** - Beautiful, easy-to-use research interface
📊 **Real-time Updates** - See research progress as it happens
📱 **Pushover Notifications** - Get notified when research is complete
🔗 **Trace Links** - Direct links to OpenAI execution traces
📝 **Full Reports** - Complete research reports displayed in browser

## Features

### Smart Content Cleaning
The Pushover agent automatically:
- Removes HTML tags
- Removes markdown formatting (headers, bold, italic)
- Cleans up excessive newlines
- Truncates long reports (>900 chars) with a notice

### Error Handling
- Returns success/error status
- Includes error details for debugging
- Prints response status to console

## Advantages over Email

- **Instant delivery** - notifications arrive within seconds
- **No spam issues** - direct push notifications to your device
- **Multi-platform** - works on mobile, desktop, and web
- **Simple setup** - just two API keys, no SMTP configuration
- **Reliable** - no email delivery issues or bounces

## Cost

Pushover has a small one-time fee per platform ($5 for mobile apps), but no ongoing API costs for normal usage.

## Contributed by Jessica Kuijer
