# WebSocket helper for Node.js

[![codecov](https://codecov.io/github/honojs/middleware/graph/badge.svg?flag=node-ws)](https://codecov.io/github/honojs/middleware)

> [!WARNING]
> **This package is deprecated.** Node.js Adapter v2 (`@hono/node-server`) now provides built-in WebSocket support via its own `upgradeWebSocket`. Please migrate to `@hono/node-server`. See [WebSocket | @hono/node-server](https://github.com/honojs/node-server#websocket-1) for details.

A WebSocket helper for Node.js

## Migration to `@hono/node-server`

Before:

```ts
import { createNodeWebSocket } from '@hono/node-ws'
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const app = new Hono()

const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app })

app.get(
  '/ws',
  upgradeWebSocket((c) => ({
    // https://hono.dev/helpers/websocket
  }))
)

const server = serve(app)
injectWebSocket(server)
```

After:

```ts
import { serve, upgradeWebSocket } from '@hono/node-server'
import { WebSocketServer } from 'ws'
import { Hono } from 'hono'

const app = new Hono()

app.get(
  '/ws',
  upgradeWebSocket((c) => ({
    // https://hono.dev/helpers/websocket
  }))
)

const wss = new WebSocketServer({ noServer: true })
serve({
  fetch: app.fetch,
  websocket: { server: wss },
})
```

## Usage

```ts
import { createNodeWebSocket } from '@hono/node-ws'
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const app = new Hono()

const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app })

app.get(
  '/ws',
  upgradeWebSocket((c) => ({
    // https://hono.dev/helpers/websocket
  }))
)

const server = serve(app)
injectWebSocket(server)
```

## Author

Shotaro Nakamura <https://github.com/nakasyou>

## License

MIT
