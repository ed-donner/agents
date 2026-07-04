'use strict'

const { version } = require('./package.json')
const { EventEmitter } = require('events')
const { Worker } = require('worker_threads')
const { join } = require('path')
const { pathToFileURL } = require('url')
const { wait } = require('./lib/wait')
const {
  WRITE_INDEX,
  READ_INDEX,
  SEQ_INDEX
} = require('./lib/indexes')
const buffer = require('buffer')
const assert = require('assert')

const kImpl = Symbol('kImpl')

// Maximum pending buffered data before forcing a synchronous drain
const MAX_STRING = buffer.constants.MAX_STRING_LENGTH

function noop () {}

function updateState (stream, fn) {
  Atomics.add(stream[kImpl].state, SEQ_INDEX, 1)
  fn()
  Atomics.add(stream[kImpl].state, SEQ_INDEX, 1)
  Atomics.notify(stream[kImpl].state, SEQ_INDEX)
}

function resetIndexes (stream) {
  updateState(stream, () => {
    Atomics.store(stream[kImpl].state, READ_INDEX, 0)
    Atomics.store(stream[kImpl].state, WRITE_INDEX, 0)
  })
}

class FakeWeakRef {
  constructor (value) {
    this._value = value
  }

  deref () {
    return this._value
  }
}

class FakeFinalizationRegistry {
  register () {}

  unregister () {}
}

// Currently using FinalizationRegistry with code coverage breaks the world
// Ref: https://github.com/nodejs/node/issues/49344
const FinalizationRegistry = process.env.NODE_V8_COVERAGE ? FakeFinalizationRegistry : global.FinalizationRegistry || FakeFinalizationRegistry
const WeakRef = process.env.NODE_V8_COVERAGE ? FakeWeakRef : global.WeakRef || FakeWeakRef

const registry = new FinalizationRegistry((worker) => {
  if (worker.exited) {
    return
  }
  worker.terminate()
})

function createWorker (stream, opts) {
  const { filename, workerData } = opts

  const bundlerOverrides = '__bundlerPathsOverrides' in globalThis ? globalThis.__bundlerPathsOverrides : {}
  const toExecute = bundlerOverrides['thread-stream-worker'] || join(__dirname, 'lib', 'worker.js')

  const worker = new Worker(toExecute, {
    ...opts.workerOpts,
    name: opts.workerOpts?.name || 'thread-stream',
    trackUnmanagedFds: false,
    workerData: {
      filename: filename.indexOf('file://') === 0
        ? filename
        : pathToFileURL(filename).href,
      dataBuf: stream[kImpl].dataBuf,
      stateBuf: stream[kImpl].stateBuf,
      workerData: {
        $context: {
          threadStreamVersion: version
        },
        ...workerData
      }
    }
  })

  // We keep a strong reference for now,
  // we need to start writing first
  worker.stream = new FakeWeakRef(stream)

  worker.on('message', onWorkerMessage)
  worker.on('exit', onWorkerExit)
  registry.register(stream, worker)

  return worker
}

function drain (stream) {
  assert(!stream[kImpl].sync)
  if (stream[kImpl].needDrain) {
    stream[kImpl].needDrain = false
    stream.emit('drain')
  }
}

function nextFlush (stream) {
  while (true) {
    const writeIndex = Atomics.load(stream[kImpl].state, WRITE_INDEX)
    const leftover = stream[kImpl].data.length - writeIndex

    if (leftover > 0) {
      if (stream[kImpl].bufLen === 0) {
        stream[kImpl].flushing = false

        if (stream[kImpl].ending) {
          end(stream)
        } else if (stream[kImpl].needDrain) {
          process.nextTick(drain, stream)
        }

        return
      }

      write(stream, leftover, noop)
      continue
    }

    if (leftover === 0) {
      if (writeIndex === 0 && stream[kImpl].bufLen === 0) {
        // we had a flushSync in the meanwhile
        return
      }
      waitForRead(stream, () => {
        if (stream.destroyed) {
          return
        }

        resetIndexes(stream)
        nextFlush(stream)
      })
      return
    }

    // This should never happen
    destroy(stream, new Error('overwritten'))
    return
  }
}

function onWorkerMessage (msg) {
  const stream = this.stream.deref()
  if (stream === undefined) {
    this.exited = true
    // Terminate the worker.
    this.terminate()
    return
  }

  // Node.js watch mode may send internal worker messages that do not
  // participate in thread-stream's worker protocol.
  if (msg?.code == null) {
    return
  }

  switch (msg.code) {
    case 'READY':
      // Replace the FakeWeakRef with a
      // proper one.
      this.stream = new WeakRef(stream)

      waitForRead(stream, () => {
        stream[kImpl].ready = true
        stream.emit('ready')
      })
      break
    case 'ERROR':
      destroy(stream, msg.err)
      break
    case 'EVENT':
      if (Array.isArray(msg.args)) {
        stream.emit(msg.name, ...msg.args)
      } else {
        stream.emit(msg.name, msg.args)
      }
      break
    case 'FLUSHED': {
      if (msg.context !== 'thread-stream') {
        destroy(stream, new Error('this should not happen: ' + msg.code))
        break
      }

      const cb = stream[kImpl].flushCallbacks.get(msg.id)
      if (cb) {
        stream[kImpl].flushCallbacks.delete(msg.id)
        process.nextTick(cb)
      }
      break
    }
    case 'WARNING':
      process.emitWarning(msg.err)
      break
    default:
      destroy(stream, new Error('this should not happen: ' + msg.code))
  }
}

function onWorkerExit (code) {
  const stream = this.stream.deref()
  if (stream === undefined) {
    // Nothing to do, the worker already exit
    return
  }
  registry.unregister(stream)
  stream.worker.exited = true
  stream.worker.off('exit', onWorkerExit)
  destroy(stream, code !== 0 ? new Error('the worker thread exited') : null)
}

class ThreadStream extends EventEmitter {
  constructor (opts = {}) {
    super()

    if (opts.bufferSize < 4) {
      throw new Error('bufferSize must at least fit a 4-byte utf-8 char')
    }

    this[kImpl] = {}
    this[kImpl].stateBuf = new SharedArrayBuffer(128)
    this[kImpl].state = new Int32Array(this[kImpl].stateBuf)
    this[kImpl].dataBuf = new SharedArrayBuffer(opts.bufferSize || 4 * 1024 * 1024)
    this[kImpl].data = Buffer.from(this[kImpl].dataBuf)
    this[kImpl].sync = opts.sync || false
    this[kImpl].ending = false
    this[kImpl].ended = false
    this[kImpl].needDrain = false
    this[kImpl].destroyed = false
    this[kImpl].flushing = false
    this[kImpl].ready = false
    this[kImpl].finished = false
    this[kImpl].errored = null
    this[kImpl].closed = false
    this[kImpl].buf = []
    this[kImpl].bufHead = 0
    this[kImpl].bufLen = 0
    this[kImpl].flushCallbacks = new Map()
    this[kImpl].nextFlushId = 0

    // TODO (fix): Make private?
    this.worker = createWorker(this, opts) // TODO (fix): make private
    this.on('message', (message, transferList) => {
      this.worker.postMessage(message, transferList)
    })
  }

  write (data) {
    const dataBuf = Buffer.isBuffer(data) ? data : Buffer.from(data)
    if (this[kImpl].destroyed) {
      error(this, new Error('the worker has exited'))
      return false
    }

    if (this[kImpl].ending) {
      error(this, new Error('the worker is ending'))
      return false
    }

    if (this[kImpl].flushing && this[kImpl].bufLen + dataBuf.length >= MAX_STRING) {
      try {
        writeSync(this)
        this[kImpl].flushing = true
      } catch (err) {
        destroy(this, err)
        return false
      }
    }

    this[kImpl].buf.push(dataBuf)
    this[kImpl].bufLen += dataBuf.length

    if (this[kImpl].sync) {
      try {
        writeSync(this)
        return true
      } catch (err) {
        destroy(this, err)
        return false
      }
    }

    if (!this[kImpl].flushing) {
      this[kImpl].flushing = true
      setImmediate(nextFlush, this)
    }

    this[kImpl].needDrain = this[kImpl].data.length - this[kImpl].bufLen - Atomics.load(this[kImpl].state, WRITE_INDEX) <= 0
    return !this[kImpl].needDrain
  }

  end () {
    if (this[kImpl].destroyed) {
      return
    }

    this[kImpl].ending = true
    end(this)
  }

  flush (cb) {
    cb = typeof cb === 'function' ? cb : noop

    flushBuffer(this, (err) => {
      if (err) {
        process.nextTick(cb, err)
        return
      }

      requestWorkerFlush(this, cb)
    })
  }

  flushSync () {
    if (this[kImpl].destroyed) {
      return
    }

    writeSync(this)
    flushSync(this)
  }

  unref () {
    this.worker.unref()
  }

  ref () {
    this.worker.ref()
  }

  get ready () {
    return this[kImpl].ready
  }

  get destroyed () {
    return this[kImpl].destroyed
  }

  get closed () {
    return this[kImpl].closed
  }

  get writable () {
    return !this[kImpl].destroyed && !this[kImpl].ending
  }

  get writableEnded () {
    return this[kImpl].ending
  }

  get writableFinished () {
    return this[kImpl].finished
  }

  get writableNeedDrain () {
    return this[kImpl].needDrain
  }

  get writableObjectMode () {
    return false
  }

  get writableErrored () {
    return this[kImpl].errored
  }
}

function flushBuffer (stream, cb) {
  if (stream[kImpl].destroyed) {
    process.nextTick(cb, new Error('the worker has exited'))
    return
  }

  if (!stream[kImpl].sync && (stream[kImpl].flushing || stream[kImpl].bufLen > 0)) {
    setImmediate(flushBuffer, stream, cb)
    return
  }

  waitForRead(stream, cb)
}

function waitForRead (stream, cb) {
  const writeIndex = Atomics.load(stream[kImpl].state, WRITE_INDEX)
  wait(stream[kImpl].state, READ_INDEX, writeIndex, Infinity, (err, res) => {
    if (err) {
      destroy(stream, err)
      cb(err)
      return
    }

    if (res !== 'ok') {
      waitForRead(stream, cb)
      return
    }

    cb()
  })
}

function requestWorkerFlush (stream, cb) {
  if (stream[kImpl].destroyed) {
    process.nextTick(cb, new Error('the worker has exited'))
    return
  }

  if (!stream[kImpl].ready) {
    const onReady = () => {
      cleanup()
      requestWorkerFlush(stream, cb)
    }
    const onClose = () => {
      cleanup()
      process.nextTick(cb, new Error('the worker has exited'))
    }
    const cleanup = () => {
      stream.off('ready', onReady)
      stream.off('close', onClose)
    }

    stream.once('ready', onReady)
    stream.once('close', onClose)
    return
  }

  const id = ++stream[kImpl].nextFlushId
  stream[kImpl].flushCallbacks.set(id, cb)

  try {
    stream.worker.postMessage({
      code: 'FLUSH',
      context: 'thread-stream',
      id
    })
  } catch (err) {
    stream[kImpl].flushCallbacks.delete(id)
    destroy(stream, err)
    process.nextTick(cb, err)
  }
}

function failPendingFlushCallbacks (stream, err) {
  const callbacks = stream[kImpl].flushCallbacks
  if (callbacks.size === 0) {
    return
  }

  const flushErr = err || new Error('the worker has exited')

  for (const cb of callbacks.values()) {
    process.nextTick(cb, flushErr)
  }
  callbacks.clear()
}

function error (stream, err) {
  setImmediate(() => {
    stream.emit('error', err)
  })
}

function destroy (stream, err) {
  if (stream[kImpl].destroyed) {
    return
  }
  stream[kImpl].destroyed = true
  failPendingFlushCallbacks(stream, err)

  if (err) {
    stream[kImpl].errored = err
    error(stream, err)
  }

  if (!stream.worker.exited) {
    stream.worker.terminate()
      .catch(() => {})
      .then(() => {
        stream[kImpl].closed = true
        stream.emit('close')
      })
  } else {
    setImmediate(() => {
      stream[kImpl].closed = true
      stream.emit('close')
    })
  }
}

function write (stream, maxBytes, cb) {
  // data is smaller than the shared buffer length
  const current = Atomics.load(stream[kImpl].state, WRITE_INDEX)
  let offset = current
  let remaining = maxBytes

  while (remaining > 0 && stream[kImpl].bufLen !== 0) {
    const head = stream[kImpl].bufHead
    const buf = stream[kImpl].buf[head]

    if (buf.length <= remaining) {
      buf.copy(stream[kImpl].data, offset)
      offset += buf.length
      remaining -= buf.length
      stream[kImpl].bufLen -= buf.length
      stream[kImpl].bufHead = head + 1

      if (stream[kImpl].bufHead === stream[kImpl].buf.length) {
        stream[kImpl].buf.length = 0
        stream[kImpl].bufHead = 0
      } else if (stream[kImpl].bufHead >= 1024 && stream[kImpl].bufHead * 2 >= stream[kImpl].buf.length) {
        stream[kImpl].buf.splice(0, stream[kImpl].bufHead)
        stream[kImpl].bufHead = 0
      }
      continue
    }

    buf.copy(stream[kImpl].data, offset, 0, remaining)
    stream[kImpl].buf[head] = buf.subarray(remaining)
    stream[kImpl].bufLen -= remaining
    offset += remaining
    remaining = 0
  }

  updateState(stream, () => {
    Atomics.store(stream[kImpl].state, WRITE_INDEX, offset)
  })
  cb()
  return true
}

function end (stream) {
  if (stream[kImpl].ended || !stream[kImpl].ending || stream[kImpl].flushing) {
    return
  }
  stream[kImpl].ended = true

  try {
    stream.flushSync()

    let readIndex = Atomics.load(stream[kImpl].state, READ_INDEX)

    // process._rawDebug('writing index')
    updateState(stream, () => {
      Atomics.store(stream[kImpl].state, WRITE_INDEX, -1)
    })
    // process._rawDebug(`(end) readIndex (${Atomics.load(stream.state, READ_INDEX)}) writeIndex (${Atomics.load(stream.state, WRITE_INDEX)})`)

    // Wait for the process to complete
    let spins = 0
    while (readIndex !== -1) {
      // process._rawDebug(`read = ${read}`)
      Atomics.wait(stream[kImpl].state, READ_INDEX, readIndex, 1000)
      readIndex = Atomics.load(stream[kImpl].state, READ_INDEX)

      if (readIndex === -2) {
        destroy(stream, new Error('end() failed'))
        return
      }

      if (++spins === 10) {
        destroy(stream, new Error('end() took too long (10s)'))
        return
      }
    }

    process.nextTick(() => {
      stream[kImpl].finished = true
      stream.emit('finish')
    })
  } catch (err) {
    destroy(stream, err)
  }
  // process._rawDebug('end finished...')
}

function writeSync (stream) {
  const cb = () => {
    if (stream[kImpl].ending) {
      end(stream)
    } else if (stream[kImpl].needDrain) {
      process.nextTick(drain, stream)
    }
  }
  stream[kImpl].flushing = false

  while (stream[kImpl].bufLen !== 0) {
    const writeIndex = Atomics.load(stream[kImpl].state, WRITE_INDEX)
    const leftover = stream[kImpl].data.length - writeIndex
    if (leftover === 0) {
      flushSync(stream)
      resetIndexes(stream)
      continue
    } else if (leftover < 0) {
      // stream should never happen
      throw new Error('overwritten')
    }

    write(stream, leftover, cb)
  }
}

function flushSync (stream) {
  if (stream[kImpl].flushing) {
    throw new Error('unable to flush while flushing')
  }

  // process._rawDebug('flushSync started')

  const writeIndex = Atomics.load(stream[kImpl].state, WRITE_INDEX)

  let spins = 0

  // TODO handle deadlock
  while (true) {
    const readIndex = Atomics.load(stream[kImpl].state, READ_INDEX)

    if (readIndex === -2) {
      throw Error('_flushSync failed')
    }

    // process._rawDebug(`(flushSync) readIndex (${readIndex}) writeIndex (${writeIndex})`)
    if (readIndex !== writeIndex) {
      // TODO stream timeouts for some reason.
      Atomics.wait(stream[kImpl].state, READ_INDEX, readIndex, 1000)
    } else {
      break
    }

    if (++spins === 10) {
      throw new Error('_flushSync took too long (10s)')
    }
  }
  // process._rawDebug('flushSync finished')
}

module.exports = ThreadStream
