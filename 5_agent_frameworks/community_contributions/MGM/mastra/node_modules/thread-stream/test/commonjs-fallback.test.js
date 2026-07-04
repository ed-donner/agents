'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { MessageChannel } = require('worker_threads')
const { once } = require('events')
const ThreadStream = require('..')

const isYarnPnp = process.versions.pnp !== undefined

test('yarn module resolution', { skip: !isYarnPnp }, (t, done) => {
  const modulePath = require.resolve('pino-elasticsearch')
  assert.match(modulePath, /.*\.zip.*/)

  const stream = new ThreadStream({
    filename: modulePath,
    workerData: { node: null },
    sync: true
  })

  assert.deepStrictEqual(stream.writableErrored, null)
  stream.on('error', (err) => {
    assert.deepStrictEqual(stream.writableErrored, err)
  })

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.writable)
  stream.end()
  done()
})

test('yarn module resolution for directories with special characters', { skip: !isYarnPnp }, async t => {
  const { port1, port2 } = new MessageChannel()
  const stream = new ThreadStream({
    filename: join(__dirname, 'dir with spaces', 'test-package.zip', 'worker.js'),
    workerData: { port: port1 },
    workerOpts: {
      transferList: [port1]
    },
    sync: false
  })
  t.after(() => {
    stream.end()
  })

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))

  const [strings] = await once(port2, 'message')

  assert.strictEqual(strings, 'hello world\nsomething else\n')
})

test('yarn module resolution for typescript commonjs modules', { skip: !isYarnPnp }, async t => {
  const { port1, port2 } = new MessageChannel()
  const stream = new ThreadStream({
    filename: join(__dirname, 'ts-commonjs-default-export.zip', 'worker.js'),
    workerData: { port: port1 },
    workerOpts: {
      transferList: [port1]
    },
    sync: false
  })
  t.after(() => {
    stream.end()
  })

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))

  const [strings] = await once(port2, 'message')

  assert.strictEqual(strings, 'hello world\nsomething else\n')
})
