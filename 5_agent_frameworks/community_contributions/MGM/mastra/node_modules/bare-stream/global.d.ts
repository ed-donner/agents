import * as web from './web'

declare global {
  type ReadableStream = web.ReadableStream
  type ReadableStreamDefaultController = web.ReadableStreamDefaultController
  type ReadableStreamDefaultReader = web.ReadableStreamDefaultReader

  type CountQueuingStrategy = web.CountQueuingStrategy
  type ByteLengthQueuingStrategy = web.ByteLengthQueuingStrategy

  type WritableStream = web.WritableStream
  type WritableStreamDefaultController = web.WritableStreamDefaultController
  type WritableStreamDefaultWriter = web.WritableStreamDefaultWriter

  type TransformStream = web.TransformStream
  type TransformStreamDefaultController = web.TransformStreamDefaultController

  const ReadableStream: typeof web.ReadableStream
  const ReadableStreamDefaultController: typeof web.ReadableStreamDefaultController
  const ReadableStreamDefaultReader: typeof web.ReadableStreamDefaultReader

  const CountQueuingStrategy: typeof web.CountQueuingStrategy
  const ByteLengthQueuingStrategy: typeof web.ByteLengthQueuingStrategy

  const WritableStream: typeof web.WritableStream
  const WritableStreamDefaultController: typeof web.WritableStreamDefaultController
  const WritableStreamDefaultWriter: typeof web.WritableStreamDefaultWriter

  const TransformStream: typeof web.TransformStream
  const TransformStreamDefaultController: typeof web.TransformStreamDefaultController
}
