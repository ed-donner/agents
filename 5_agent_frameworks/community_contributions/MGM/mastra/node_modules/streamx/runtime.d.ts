type BufferEncoding =
  | 'ascii'
  | 'base64'
  | 'binary'
  | 'hex'
  | 'latin1'
  | 'ucs-2'
  | 'ucs2'
  | 'utf-16le'
  | 'utf-8'
  | 'utf16le'
  | 'utf8'

interface EventMap {
  [event: string | symbol]: unknown[]
}

interface EventHandler<in A extends unknown[] = unknown[], out R = unknown> {
  (...args: A): R
}

interface EventEmitter<in out M extends EventMap = EventMap> {
  addListener<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  addOnceListener<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  prependListener<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  prependOnceListener<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  removeListener<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  removeAllListeners<E extends keyof M>(name?: E): this

  on<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  once<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  off<E extends keyof M, R>(name: E, fn: EventHandler<M[E], R>): this

  emit<E extends keyof M>(name: E, ...args: M[E]): boolean

  listeners<E extends keyof M, R>(name: E): EventHandler<M[E], R>

  rawListeners<E extends keyof M, R>(name: E): EventHandler<M[E], R>[]

  eventNames(): (keyof M)[]

  listenerCount<E extends keyof M>(name: E): number

  getMaxListeners(): number
  setMaxListeners(n: number): void
}

export { BufferEncoding, EventMap, EventEmitter }
