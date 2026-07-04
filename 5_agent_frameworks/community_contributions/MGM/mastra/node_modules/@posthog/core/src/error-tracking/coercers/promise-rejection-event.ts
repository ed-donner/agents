// Portions of this file are derived from getsentry/sentry-javascript
// Copyright (c) 2012 Functional Software, Inc. dba Sentry
// Licensed under the MIT License: https://github.com/getsentry/sentry-javascript/blob/develop/LICENSE

import { isBuiltin, isEvent, isPrimitive } from '@/utils'
import { CoercingContext, ErrorTrackingCoercer, ExceptionLike } from '../types'

// Structural subsets of the DOM `PromiseRejectionEvent` / `Event`. Avoids leaking
// DOM-only globals into the public type surface so non-DOM consumers (e.g. React
// Native, whose tsconfig lib excludes DOM) can still consume `@posthog/core`
// types via tools like api-extractor that resolve symbols transitively.
interface PromiseRejectionEventLike {
  reason: unknown
}
interface EventWithDetailReason {
  detail: { reason: unknown }
}
type RejectionLike = PromiseRejectionEventLike | EventWithDetailReason

// Web only
export class PromiseRejectionEventCoercer implements ErrorTrackingCoercer<RejectionLike> {
  match(err: unknown): err is RejectionLike {
    return isBuiltin(err, 'PromiseRejectionEvent') || this.isCustomEventWrappingRejection(err)
  }

  private isCustomEventWrappingRejection(err: unknown): err is EventWithDetailReason {
    if (!isEvent(err)) {
      return false
    }
    try {
      const detail = (err as unknown as EventWithDetailReason).detail
      return detail != null && typeof detail === 'object' && 'reason' in detail
    } catch {
      return false
    }
  }

  coerce(err: RejectionLike, ctx: CoercingContext): ExceptionLike | undefined {
    const reason = this.getUnhandledRejectionReason(err)
    if (isPrimitive(reason)) {
      return {
        type: 'UnhandledRejection',
        value: `Non-Error promise rejection captured with value: ${String(reason)}`,
        stack: ctx.syntheticException?.stack,
        synthetic: true,
      }
    } else {
      return ctx.apply(reason)
    }
  }

  private getUnhandledRejectionReason(error: RejectionLike): unknown {
    try {
      // PromiseRejectionEvents store the object of the rejection under 'reason'
      // see https://developer.mozilla.org/en-US/docs/Web/API/PromiseRejectionEvent
      if ('reason' in error) {
        return error.reason
      }

      // something, somewhere, (likely a browser extension) effectively casts PromiseRejectionEvents
      // to CustomEvents, moving the `promise` and `reason` attributes of the PRE into
      // the CustomEvent's `detail` attribute, since they're not part of CustomEvent's spec
      // Unwrap `detail.reason` so extension errors are reported as the original Error instead of
      // a generic CustomEvent with keys like currentTarget, detail, isTrusted, and target.
      // see https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent
      if ('detail' in error && error.detail != null && typeof error.detail === 'object' && 'reason' in error.detail) {
        return error.detail.reason
      }
    } catch {
      // no-empty
    }

    return error
  }
}
