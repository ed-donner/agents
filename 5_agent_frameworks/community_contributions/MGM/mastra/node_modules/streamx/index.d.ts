import { BufferEncoding, EventMap, EventEmitter } from './runtime'

interface StreamCallback {
  (err: Error | null): void
}

type Pipeline<S extends Writable> = [src: Readable, ...transforms: Duplex[], dest: S]

declare function pipeline<S extends Writable>(streams: Pipeline<S>, cb?: StreamCallback): S
declare function pipeline<S extends Writable>(...args: Pipeline<S>): S
declare function pipeline<S extends Writable>(...args: [...Pipeline<S>, cb: StreamCallback]): S

declare function pipelinePromise<S extends Writable>(...args: Pipeline<S>): Promise<S>

declare function isStream(stream: Stream): stream is Stream
declare function isStreamx(stream: Stream): boolean
declare function isEnding(stream: Stream): boolean
declare function isEnded(stream: Stream): boolean
declare function isFinishing(stream: Stream): boolean
declare function isFinished(stream: Stream): boolean
declare function isDisturbed(stream: Stream): boolean

interface GetStreamErrorOptions {
  all?: boolean
}

declare function getStreamError(stream: Stream, opts?: GetStreamErrorOptions): Error | null

interface StreamEvents extends EventMap {
  close: []
  error: [err: Error]
}

interface StreamOptions<S extends Stream = Stream> {
  byteLength?(data: unknown): number
  destroy?(this: S, cb: StreamCallback): void
  eagerOpen?: boolean
  highWaterMark?: number
  map?(data: unknown): unknown
  open?(this: S, cb: StreamCallback): void
  predestroy?(this: S): void
  signal?: AbortSignal
}

interface Stream<M extends StreamEvents = StreamEvents> extends EventEmitter<M> {
  _open(cb: StreamCallback): void
  _predestroy(): void
  _destroy(cb: StreamCallback): void

  readonly readable: boolean
  readonly writable: boolean
  readonly destroyed: boolean
  readonly destroying: boolean

  destroy(err?: Error | null): void
}

declare class Stream {
  constructor(opts?: StreamOptions)
}

interface WritableEvents extends StreamEvents {
  drain: []
  finish: []
  pipe: [src: Readable]
}

interface WritableOptions<S extends Writable = Writable> extends StreamOptions<S> {
  byteLengthWritable?(data: unknown): number
  final?(this: S, cb: StreamCallback): void
  mapWritable?(data: unknown): unknown
  write?(this: S, data: unknown, cb: StreamCallback): void
  writev?(this: S, batch: unknown[], cb: StreamCallback): void
}

interface Writable<M extends WritableEvents = WritableEvents> extends Stream<M> {
  _write(data: unknown, cb: StreamCallback): void
  _writev(batch: unknown[], cb: StreamCallback): void
  _final(cb: StreamCallback): void

  write(data: unknown): unknown

  end(data: unknown): this

  cork(): void
  uncork(): void
}

declare class Writable<M extends WritableEvents = WritableEvents> extends Stream<M> {
  constructor(opts?: WritableOptions)

  static isBackpressured(ws: Writable): boolean

  static drained(ws: Writable): Promise<unknown>
}

interface ReadableEvents extends StreamEvents {
  data: [data: unknown]
  end: []
  piping: [dest: Writable]
  readable: []
}

interface ReadableOptions<S extends Readable = Readable> extends StreamOptions<S> {
  byteLengthReadable?(data: unknown): number
  encoding?: BufferEncoding
  mapReadable?(data: unknown): unknown
  read?(this: S, cb: StreamCallback): void
}

interface Readable<M extends ReadableEvents = ReadableEvents>
  extends Stream<M>, AsyncIterable<unknown> {
  _read(cb: StreamCallback): void

  push(data: unknown | null): boolean
  unshift(data: unknown | null): void
  read(): unknown | null

  resume(): this
  pause(): this

  pipe<S extends Writable>(dest: S, cb?: StreamCallback): S

  setEncoding(encoding: BufferEncoding): this
}

declare class Readable<M extends ReadableEvents = ReadableEvents> extends Stream<M> {
  constructor(opts?: ReadableOptions)

  static deferred(fn: () => Promise<Readable>, opts?: TransformOptions): Transform

  static from(data: unknown | unknown[] | AsyncIterable<unknown>, opts?: ReadableOptions): Readable

  static isBackpressured(rs: Readable): boolean

  static isPaused(rs: Readable): boolean
}

interface DuplexEvents extends ReadableEvents, WritableEvents {}

interface DuplexOptions<S extends Duplex = Duplex> extends ReadableOptions<S>, WritableOptions<S> {}

interface Duplex<M extends DuplexEvents = DuplexEvents> extends Readable<M>, Writable<M> {}

declare class Duplex<M extends DuplexEvents = DuplexEvents> extends Stream<M> {
  constructor(opts?: DuplexOptions)
}

interface TransformCallback {
  (err: Error | null, mappedData: unknown): void
}

interface TransformEvents extends DuplexEvents {}

interface TransformOptions<S extends Transform = Transform> extends DuplexOptions<S> {
  flush?(this: S, cb: StreamCallback): void
  transform?(this: S, data: unknown, cb: TransformCallback): void
}

interface Transform<M extends TransformEvents = TransformEvents> extends Duplex<M> {
  _flush(cb: StreamCallback): void
  _transform(Data: unknown, cb: TransformCallback): void
}

declare class Transform<M extends TransformEvents = TransformEvents> extends Duplex<M> {
  constructor(opts?: TransformOptions)
}

export {
  type Pipeline,
  pipeline,
  pipelinePromise,
  isStream,
  isStreamx,
  isEnding,
  isEnded,
  isFinishing,
  isFinished,
  isDisturbed,
  type GetStreamErrorOptions,
  getStreamError,
  type StreamEvents,
  type StreamOptions,
  Stream,
  type WritableEvents,
  type WritableOptions,
  Writable,
  type ReadableEvents,
  type ReadableOptions,
  Readable,
  type DuplexEvents,
  type DuplexOptions,
  Duplex,
  type TransformEvents,
  type TransformOptions,
  Transform,
  Transform as PassThrough
}
