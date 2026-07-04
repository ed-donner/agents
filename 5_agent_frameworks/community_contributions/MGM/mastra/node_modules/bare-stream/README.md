# bare-stream

Streaming data for JavaScript. The classic Node.js-style stream classes are backed by `streamx` (<https://github.com/mafintosh/streamx>) while a `node:stream/web`-compatible implementation of the WHATWG Streams Standard is also provided.

```
npm i bare-stream
```

## Usage

```js
const { Readable } = require('bare-stream')

const stream = new Readable({
  read(size) {
    // Push data, then push `null` to signal the end
    this.push('hello')
    this.push('world')
    this.push(null)
  }
})

stream.on('data', (data) => console.log(data))
```

## API

The classic stream classes and helpers are exported from `bare-stream` and follow the Node.js `stream` API. See <https://nodejs.org/api/stream.html> and <https://github.com/mafintosh/streamx> for the complete behavior; the additions and differences specific to this module are documented below.

#### `const stream = new Readable([options])`

A readable stream. Options include:

```js
options = {
  eagerOpen: false,
  highWaterMark: 16384,
  encoding: null,
  signal: null,
  open(cb) {},
  read(size) {},
  predestroy() {},
  destroy(err, cb) {}
}
```

If `encoding` is set, emitted data is decoded to strings using that encoding. If `signal` is an `AbortSignal`, the stream is destroyed when the signal aborts.

#### `stream.closed`

`true` when the stream is no longer readable.

#### `stream.errored`

The error the stream was destroyed with, or `null`.

#### `stream.push(data[, encoding])`

Push `data` into the stream's internal buffer. If `data` is a string, it is encoded to a `Buffer` using `encoding`, defaulting to `'utf8'`. Push `null` to signal the end of the stream.

#### `stream.unshift(data[, encoding])`

Like `stream.push()` but prepends `data` to the internal buffer so it is read before any already buffered data.

#### `Readable.from(data[, options])`

Create a readable stream from `data`, which may be a value, an array of values, or an async iterable.

#### `Readable.isBackpressured(stream)`

#### `Readable.isPaused(stream)`

#### `Readable.fromWeb(readableStream[, options])`

Convert a web `ReadableStream` into a `Readable`. Options include:

```js
options = {
  encoding: null,
  signal: null
}
```

#### `Readable.toWeb(readable[, options])`

Convert a `Readable` into a web `ReadableStream`. Options include:

```js
options = {
  strategy: null
}
```

`strategy` is a custom queuing strategy passed through to the `ReadableStream` constructor.

#### `const stream = new Writable([options])`

A writable stream. Options include:

```js
options = {
  eagerOpen: false,
  signal: null,
  open(cb) {},
  write(data, encoding, cb) {},
  writev(batch, cb) {},
  final(cb) {},
  predestroy() {},
  destroy(err, cb) {}
}
```

#### `stream.closed`

`true` when the stream is no longer writable.

#### `stream.errored`

The error the stream was destroyed with, or `null`.

#### `stream.write(data[, encoding][, cb])`

Write `data` to the stream. If `data` is a string, it is encoded using `encoding`, defaulting to `'utf8'`. Returns `false` if the stream is backpressured. The optional `cb` is called once the write has drained.

#### `stream.end([data][, encoding][, cb])`

Signal that no more data will be written. If `data` is provided it is written first. The optional `cb` is called once the stream has finished.

#### `Writable.isBackpressured(stream)`

#### `Writable.drained(stream)`

Returns a promise that resolves once the stream has drained.

#### `Writable.fromWeb(writableStream[, options])`

Convert a web `WritableStream` into a `Writable`. Options include:

```js
options = {
  signal: null
}
```

#### `Writable.toWeb(writable)`

Convert a `Writable` into a web `WritableStream`.

#### `const stream = new Duplex([options])`

A stream that is both readable and writable. Accepts the combined options of `Readable` and `Writable`.

#### `Duplex.fromWeb({ readable, writable }[, options])`

Convert a pair of web `ReadableStream` and `WritableStream` into a `Duplex`.

#### `Duplex.toWeb(duplex)`

Convert a `Duplex` into a `{ readable, writable }` pair of web streams.

#### `const stream = new Transform([options])`

A duplex stream where output is computed from input. Options include the `Duplex` options plus:

```js
options = {
  transform(data, encoding, cb) {},
  flush(cb) {}
}
```

If no `transform` is provided, the stream acts as a pass-through.

#### `const stream = new PassThrough([options])`

A `Transform` that forwards input to output unchanged.

#### `const [a, b] = duplexPair([options])`

Create a pair of linked `Duplex` streams. Data written to `a` is readable from `b` and vice versa. `options` are passed to each side.

#### `stream.pipeline(streams[, cb])`

#### `stream.pipeline(...streams[, cb])`

Pipe a series of streams together, propagating errors and cleaning up on completion. `streams` is a `Readable` source, zero or more `Duplex` transforms, and a `Writable` destination. Returns the destination stream. `cb` is called when the pipeline finishes or errors.

#### `const detach = stream.finished(stream[, options], cb)`

Invoke `cb` once `stream` is no longer readable or writable, or has errored. Returns a function that detaches the listeners. Options include:

```js
options = {
  cleanup: false
}
```

When `cleanup` is `true`, the listeners are detached automatically once `cb` runs.

#### `stream.addAbortSignal(signal, stream)`

Destroy `stream` when `signal` aborts, using `signal.reason` as the destruction error. Returns `stream`.

#### `stream.isStream(stream)`

#### `stream.isEnding(stream)`

#### `stream.isEnded(stream)`

#### `stream.isFinishing(stream)`

#### `stream.isFinished(stream)`

#### `stream.isDisturbed(stream)`

#### `stream.isErrored(stream)`

#### `stream.isReadable(stream)`

#### `stream.isWritable(stream)`

State predicates for streams. Each returns a boolean.

#### `const err = stream.getStreamError(stream[, options])`

Return the error a stream was destroyed with, or `null`. Options include:

```js
options = {
  all: false
}
```

### Promises

A promise-based variant of `pipeline` is available from `bare-stream/promises`.

#### `const stream = await pipeline(streams)`

#### `const stream = await pipeline(...streams)`

Like `stream.pipeline()` but returns a promise that resolves with the destination stream once the pipeline finishes, or rejects on error.

### Web

A `node:stream/web`-compatible implementation of the WHATWG Streams Standard is available from `bare-stream/web`. See <https://streams.spec.whatwg.org> for the complete behavior.

#### `const stream = new ReadableStream([underlyingSource][, queuingStrategy])`

A web readable stream. `underlyingSource` may provide `start`, `pull`, and `cancel` methods, or be an existing `streamx` stream to wrap. `queuingStrategy` defaults to a `CountQueuingStrategy`.

#### `stream.locked`

#### `stream.getReader()`

Acquire a `ReadableStreamDefaultReader`. Throws if the stream is already locked.

#### `stream.cancel([reason])`

#### `stream.tee()`

Split the stream into two independent `ReadableStream` branches.

#### `stream.pipeTo(destination)`

Pipe the stream to a `WritableStream`, returning a promise that resolves once piping completes.

#### `ReadableStream.from(iterable)`

Create a `ReadableStream` from an iterable or async iterable.

#### `const reader = new ReadableStreamDefaultReader(stream)`

A reader over a `ReadableStream`, exposing `closed`, `read()`, `releaseLock()`, and `cancel([reason])`.

#### `const controller = new ReadableStreamDefaultController(stream)`

The controller passed to `start` and `pull`, exposing `desiredSize`, `enqueue(data)`, `close()`, and `error([err])`.

#### `const stream = new WritableStream([underlyingSink][, queuingStrategy])`

A web writable stream. `underlyingSink` may provide `start`, `write`, `close`, and `abort` methods, or be an existing `streamx` stream to wrap.

#### `stream.locked`

#### `stream.getWriter()`

Acquire a `WritableStreamDefaultWriter`. Throws if the stream is already locked.

#### `stream.abort([reason])`

#### `stream.close()`

#### `const writer = new WritableStreamDefaultWriter(stream)`

A writer over a `WritableStream`, exposing `desiredSize`, `closed`, `ready`, `write(chunk)`, `releaseLock()`, `close()`, and `abort([reason])`.

#### `const controller = new WritableStreamDefaultController(stream)`

The controller passed to `start` and `write`, exposing `error([err])`.

#### `const stream = new TransformStream([transformer][, writableStrategy][, readableStrategy])`

A web transform stream. `transformer` may provide `start`, `transform`, and `flush` methods. Exposes `readable` and `writable` properties.

#### `const controller = new TransformStreamDefaultController(stream)`

The controller passed to `start`, `transform`, and `flush`, exposing `desiredSize`, `enqueue(data)`, `error([err])`, and `terminate()`.

#### `const strategy = new CountQueuingStrategy([options])`

A queuing strategy that counts each chunk as size `1`. Options include:

```js
options = {
  highWaterMark: 1
}
```

#### `const strategy = new ByteLengthQueuingStrategy([options])`

A queuing strategy that measures each chunk by its `byteLength`. Options include:

```js
options = {
  highWaterMark: 16384
}
```

#### `isReadableStream(value)`

#### `isReadableStreamErrored(stream)`

#### `isReadableStreamDisturbed(stream)`

#### `isWritableStream(value)`

#### `isTransformStream(value)`

Predicates for web streams. Each returns a boolean.

### Global

Requiring `bare-stream/global` installs the web stream classes as globals, matching the browser and Node.js environments:

```js
require('bare-stream/global')

const stream = new ReadableStream()
```

## License

Apache-2.0
