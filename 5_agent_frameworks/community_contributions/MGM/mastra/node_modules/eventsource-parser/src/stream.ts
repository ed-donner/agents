import {createParser} from './parse.ts'
import type {EventSourceMessage, EventSourceParser} from './types.ts'

/**
 * Options for the EventSourceParserStream.
 *
 * @public
 */
export interface StreamOptions {
  /**
   * Behavior when a parsing error occurs.
   *
   * - A custom function can be provided to handle the error.
   * - `'terminate'` will error the stream and stop parsing.
   * - Any other value will ignore the error and continue parsing.
   *
   * @defaultValue `undefined`
   */
  onError?: ('terminate' | ((error: Error) => void)) | undefined

  /**
   * Callback for when a reconnection interval is sent from the server.
   *
   * @param retry - The number of milliseconds to wait before reconnecting.
   */
  onRetry?: ((retry: number) => void) | undefined

  /**
   * Callback for when a comment is encountered in the stream.
   *
   * @param comment - The comment encountered in the stream.
   */
  onComment?: ((comment: string) => void) | undefined

  /**
   * Maximum number of characters the parser is allowed to buffer across calls to `feed()`.
   * See {@link ParserConfig.maxBufferSize} for details.
   *
   * When the limit is exceeded, the stream is always errored (regardless of the `onError`
   * setting) since the underlying parser is unrecoverable without a `reset()`.
   *
   * @defaultValue `undefined` (unbounded)
   */
  maxBufferSize?: number | undefined
}

/**
 * A TransformStream that ingests a stream of strings and produces a stream of `EventSourceMessage`.
 *
 * @example Basic usage
 * ```
 * const eventStream =
 *   response.body
 *     .pipeThrough(new TextDecoderStream())
 *     .pipeThrough(new EventSourceParserStream())
 * ```
 *
 * @example Terminate stream on parsing errors
 * ```
 * const eventStream =
 *  response.body
 *   .pipeThrough(new TextDecoderStream())
 *   .pipeThrough(new EventSourceParserStream({onError: 'terminate'}))
 * ```
 *
 * @public
 */
export class EventSourceParserStream extends TransformStream<string, EventSourceMessage> {
  constructor({onError, onRetry, onComment, maxBufferSize}: StreamOptions = {}) {
    let parser!: EventSourceParser

    super({
      start(controller) {
        parser = createParser({
          onEvent: (event) => {
            controller.enqueue(event)
          },
          onError(error) {
            if (typeof onError === 'function') {
              onError(error)
            }

            // `max-buffer-size-exceeded` is fatal — the parser is unusable until
            // `reset()`, which the stream wrapper has no way to call. Always
            // terminate the stream in that case so consumers see the meaningful
            // `ParseError` instead of an opaque "cannot feed terminated parser"
            // throw from the next chunk.
            if (onError === 'terminate' || error.type === 'max-buffer-size-exceeded') {
              controller.error(error)
            }

            // Ignore by default
          },
          onRetry,
          onComment,
          maxBufferSize,
        })
      },
      transform(chunk) {
        parser.feed(chunk)
      },
    })
  }
}

export {type ErrorType, ParseError} from './errors.ts'
export type {EventSourceMessage} from './types.ts'
