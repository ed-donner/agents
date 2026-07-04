'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { readFile } = require('fs')
const { file } = require('./helper')
const ThreadStream = require('..')
const { MessageChannel } = require('worker_threads')
const { once } = require('events')

test('base sync=true', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: true
  })

  assert.deepStrictEqual(stream.writableObjectMode, false)

  assert.deepStrictEqual(stream.writableFinished, false)
  stream.on('finish', () => {
    assert.deepStrictEqual(stream.writableFinished, true)
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, 'hello world\nsomething else\n')
    })
  })

  assert.deepStrictEqual(stream.closed, false)
  stream.on('close', () => {
    assert.deepStrictEqual(stream.closed, true)
    assert.ok(!stream.writable)
    done()
  })

  assert.deepStrictEqual(stream.writableNeedDrain, false)
  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))
  assert.ok(stream.writable)

  assert.deepStrictEqual(stream.writableEnded, false)
  stream.end()
  assert.deepStrictEqual(stream.writableEnded, true)
})

test('overflow sync=true', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 128,
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: true
  })

  let count = 0

  // Write 10 chars, 20 times
  function write () {
    if (count++ === 20) {
      stream.end()
      return
    }

    stream.write('aaaaaaaaaa')
    // do not wait for drain event
    setImmediate(write)
  }

  write()

  stream.on('close', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data.length, 200)
      done()
    })
  })
})

test('overflow sync=false', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 128,
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  let count = 0

  assert.deepStrictEqual(stream.writableNeedDrain, false)

  // Write 10 chars, 20 times
  function write () {
    if (count++ === 20) {
      stream.end()
      return
    }

    if (!stream.write('aaaaaaaaaa')) {
      assert.deepStrictEqual(stream.writableNeedDrain, true)
    }
    // do not wait for drain event
    setImmediate(write)
  }

  write()

  stream.on('drain', () => {
    assert.deepStrictEqual(stream.writableNeedDrain, false)
  })

  stream.on('close', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data.length, 200)
      done()
    })
  })
})

test('over the bufferSize at startup', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 10,
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: true
  })

  stream.on('finish', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, 'hello world\nsomething else\n')
    })
  })

  stream.on('close', () => {
    done()
  })

  assert.ok(stream.write('hello'))
  assert.ok(stream.write(' world\n'))
  assert.ok(stream.write('something else\n'))

  stream.end()
})

test('over the bufferSize at startup (async)', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 10,
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  assert.ok(stream.write('hello'))
  assert.ok(!stream.write(' world\n'))
  assert.ok(!stream.write('something else\n'))

  stream.end()

  stream.on('finish', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, 'hello world\nsomething else\n')
    })
  })

  stream.on('close', () => {
    done()
  })
})

test('flushSync sync=false', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 128,
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  stream.on('drain', () => {
    stream.end()
  })

  stream.on('close', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data.length, 200)
      done()
    })
  })

  for (let count = 0; count < 20; count++) {
    stream.write('aaaaaaaaaa')
  }
  stream.flushSync()
})

test('pass down MessagePorts', async function (t) {
  const { port1, port2 } = new MessageChannel()
  const stream = new ThreadStream({
    filename: join(__dirname, 'port.js'),
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

test('destroy does not error', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  stream.on('ready', () => {
    stream.worker.terminate()
  })

  stream.on('error', (err) => {
    assert.strictEqual(err.message, 'the worker thread exited')
    stream.flush((err) => {
      assert.strictEqual(err.message, 'the worker has exited')
    })
    assert.doesNotThrow(() => stream.flushSync())
    assert.doesNotThrow(() => stream.end())
    done()
  })
})

test('syntax error', function (t, done) {
  const stream = new ThreadStream({
    filename: join(__dirname, 'syntax-error.mjs')
  })

  stream.on('error', (err) => {
    assert.strictEqual(err.message, 'Unexpected end of input')
    done()
  })
})
