How to Use Telegram for Notifications (Free Alternative)

If you prefer not to use Pushover, you can use a Telegram Bot to receive notifications from your AI Agent. It is free, secure, and requires no trial periods.

## Step 1: Create the Bot

1.  Open Telegram and search for **@BotFather**.
2.  Click **Start** (or type `/start`).
3.  Send the command: `/newbot`
4.  Follow the instructions:
    * **Name:** Give it a display name (e.g., "My AI Assistant").
    * **Username:** Choose a unique username ending in `bot` (e.g., `DanielAI_CourseBot`).
5.  **BotFather** will generate a **TOKEN** (it looks like `123456:ABC-Def...`).
    * 👉 **Copy this Token.**

## Step 2: Get your Chat ID

To send messages *to you*, the bot needs your personal address (Chat ID).

1.  Open Telegram and search for the **username of the bot you just created**.
2.  Click **Start** and send a simple message like "Hello".
    * *Important: You must message the bot first so it has permission to reply to you.*
3.  Open your web browser and visit this URL (replace `<YOUR_TOKEN>` with the token from Step 1):
    `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4.  You will see a text response (JSON). Look for the `"chat"` section and find the `"id"`. It will be a number (e.g., `987654321`).
    * 👉 **Copy this Number.**

## Step 3: Configure Environment Variables

Open your `.env` file and replace the Pushover variables with these two:
TELEGRAM_TOKEN=your_token_pasted_here
TELEGRAM_CHAT_ID=your_chat_id_pasted_here
