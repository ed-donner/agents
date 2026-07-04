'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { once } = require('events')
const { MessageChannel } = require('worker_threads')
const ThreadStream = require('..')

test('message events emitted on the stream are posted to the worker', async function (t) {
  const { port1, port2 } = new MessageChannel()
  const stream = new ThreadStream({
    filename: join(__dirname, 'on-message.js'),
    sync: false
  })
  t.after(() => {
    stream.end()
  })

  stream.emit('message', { text: 'hello', takeThisPortPlease: port1 }, [port1])
  const [confirmation] = await once(port2, 'message')
  assert.strictEqual(confirmation, 'received: hello')
})
