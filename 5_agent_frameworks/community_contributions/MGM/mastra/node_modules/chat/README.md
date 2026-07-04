# chat

[![npm version](https://img.shields.io/npm/v/chat)](https://www.npmjs.com/package/chat)
[![npm downloads](https://img.shields.io/npm/dm/chat)](https://www.npmjs.com/package/chat)

Core SDK for building multi-platform chat bots. Provides the `Chat` class, event handlers, JSX card runtime, emoji helpers, and type-safe message formatting.

## Installation

```bash
npm install chat
```

## Usage

```typescript
import { Chat } from "chat";
import { createSlackAdapter } from "@chat-adapter/slack";
import { createRedisState } from "@chat-adapter/state-redis";

const bot = new Chat({
  userName: "mybot",
  adapters: {
    slack: createSlackAdapter({
      botToken: process.env.SLACK_BOT_TOKEN!,
      signingSecret: process.env.SLACK_SIGNING_SECRET!,
    }),
  },
  state: createRedisState({ url: process.env.REDIS_URL! }),
  dedupeTtlMs: 600_000, // 10 minutes (default: 5 min)
});

bot.onNewMention(async (thread) => {
  await thread.subscribe();
  await thread.post("Hello! I'm listening to this thread.");
});

bot.onSubscribedMessage(async (thread, message) => {
  await thread.post(`You said: ${message.text}`);
});
```

> **Tip:** PostgreSQL and ioredis adapters are also available for production. See [State Adapters](https://chat-sdk.dev/docs/state) for all options.

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `userName` | `string` | **required** | Default bot username across all adapters |
| `adapters` | `Record<string, Adapter>` | **required** | Map of adapter name to adapter instance |
| `state` | `StateAdapter` | **required** | State adapter for subscriptions, locking, and dedup |
| `logger` | `Logger \| LogLevel` | `"info"` | Logger instance or log level (`"silent"` to disable) |
| `streamingUpdateIntervalMs` | `number` | `500` | Update interval for fallback streaming (post + edit) in ms |
| `dedupeTtlMs` | `number` | `300000` | TTL for message deduplication entries in ms. Increase if webhook cold starts cause platform retries (e.g., Slack's `http_timeout` retry) that arrive after the default window |

## AI coding agent support

If you use an AI coding agent like [Claude Code](https://docs.anthropic.com/en/docs/claude-code), you can teach it about Chat SDK:

```bash
npx skills add vercel/chat
```

## Documentation

Full documentation is available at [chat-sdk.dev/docs](https://chat-sdk.dev/docs).

- [Usage](https://chat-sdk.dev/docs/usage) — event handlers, threads, messages, channels
- [Chat API](https://chat-sdk.dev/docs/api/chat) — full `Chat` class reference
- [Cards](https://chat-sdk.dev/docs/cards) — JSX-based interactive cards
- [Streaming](https://chat-sdk.dev/docs/streaming) — AI SDK integration
- [Emoji](https://chat-sdk.dev/docs/emoji) — cross-platform emoji helpers

## License

MIT
