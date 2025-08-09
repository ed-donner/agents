## Reason

I wanted to receive notifications even after 30 days. That's why I decided to use discord webhooks instead of pushover. The code is not much different.

Steps:

1. Open discord and create a new channel in the server you want to do this in.
2. Go to `Edit Channel (gear icon)` -> `Integrations` -> `Create Webhook`.
3. Create a new webhook and give it a name.
4. Copy the webhook URL.
5. Replace pushover environment variables with `DISCORD_WEBHOOK_URL`.

Just instead of 
```py
requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )
```

We use 
```py
discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

if discord_webhook_url:
    print(f"Discord webhook URL found and starts with {discord_webhook_url[0]}")
else:
    print("Discord webhook URL not found")

def push(message):
    print(f"Discord: {message}")
    payload = {"content": message}
    requests.post(discord_webhook_url, data=payload)
```