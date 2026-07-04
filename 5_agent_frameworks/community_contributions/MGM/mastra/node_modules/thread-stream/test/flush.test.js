'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { once } = require('node:events')
const { join } = require('node:path')
const ThreadStream = require('..')

function createStream (mode) {
  return new ThreadStream({
    filename: join(__dirname, 'flush-worker.js'),
    workerData: { mode },
    sync: false
  })
}

test('flush waits for worker destination.flush(cb)', async function () {
  const stream = createStream('flush')
  let flushed = false

  stream.on('destination-flushed', () => {
    flushed = true
  })

  assert.ok(stream.write('hello'))

  await new Promise((resolve, reject) => {
    stream.flush((err) => {
      if (err) {
        reject(err)
        return
      }
      resolve()
    })
  })

  assert.strictEqual(flushed, true)

  const close = once(stream, 'close')
  stream.end()
  await close
})

test('flush falls back to destination.flushSync()', async function () {
  const stream = createStream('flush-sync')
  let called = false

  stream.on('destination-flush-sync', () => {
    called = true
  })

  assert.ok(stream.write('hello'))

  await new Promise((resolve, reject) => {
    stream.flush((err) => {
      if (err) {
        reject(err)
        return
      }
      resolve()
    })
  })

  assert.strictEqual(called, true)

  const close = once(stream, 'close')
  stream.end()
  await close
})

test('flush waits for drain when destination has no flush API', async function () {
  const stream = createStream('drain')
  let drained = false

  stream.on('destination-drain', () => {
    drained = true
  })

  assert.ok(stream.write('hello'))

  await new Promise((resolve, reject) => {
    stream.flush((err) => {
      if (err) {
        reject(err)
        return
      }
      resolve()
    })
  })

  assert.strictEqual(drained, true)

  const close = once(stream, 'close')
  stream.end()
  await close
})

test('pending flush callbacks fail when worker exits', async function () {
  const stream = createStream('exit-on-flush')
  const close = once(stream, 'close')

  assert.ok(stream.write('hello'))

  const err = await new Promise((resolve) => {
    stream.flush(resolve)
  })

  assert.ok(err)
  assert.strictEqual(err.message, 'the worker has exited')

  await close
})
