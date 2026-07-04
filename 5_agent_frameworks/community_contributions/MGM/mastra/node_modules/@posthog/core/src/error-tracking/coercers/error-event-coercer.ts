import { CoercingContext, ErrorTrackingCoercer, ExceptionLike } from '../types'
import { isErrorEvent } from '@/utils'

// Structural subset of the DOM `ErrorEvent`. Avoids leaking a DOM-only global
// into the public type surface so non-DOM consumers (e.g. React Native, whose
// tsconfig lib excludes DOM) can still consume `@posthog/core` types via tools
// like api-extractor that resolve symbols transitively.
interface ErrorEventLike {
  message: string
  error?: unknown
}

export class ErrorEventCoercer implements ErrorTrackingCoercer<ErrorEventLike> {
  constructor() {}

  match(err: unknown): err is ErrorEventLike {
    return isErrorEvent(err) && (err as ErrorEventLike).error != undefined
  }

  coerce(err: ErrorEventLike, ctx: CoercingContext): ExceptionLike {
    const exceptionLike = ctx.apply(err.error)
    if (!exceptionLike) {
      return {
        type: 'ErrorEvent',
        value: err.message,
        stack: ctx.syntheticException?.stack,
        synthetic: true,
      }
    } else {
      return exceptionLike
    }
  }
}
