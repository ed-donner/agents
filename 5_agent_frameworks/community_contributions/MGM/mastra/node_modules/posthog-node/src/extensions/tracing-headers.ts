import type { IncomingHttpHeaders } from 'node:http'

const TRACING_HEADER_MAX_LENGTH = 1000
// Remove C0 controls, DEL, and C1 controls from PostHog tracing IDs only.
// eslint-disable-next-line no-control-regex
const TRACING_HEADER_CONTROL_CHARS_REGEX = /[\x00-\x1f\x7f-\x9f]/g

type HeaderValue = IncomingHttpHeaders[string]

export const POSTHOG_TRACING_HEADERS = {
  sessionId: 'x-posthog-session-id',
  distinctId: 'x-posthog-distinct-id',
} as const

export interface PostHogTracingHeaderValues {
  sessionId?: string
  distinctId?: string
}

export function addProperty(properties: Record<string, any>, key: string, value: unknown): void {
  if (value !== undefined && value !== null && value !== '') {
    properties[key] = value
  }
}

export function getFirstHeaderValue(value: HeaderValue): string | undefined {
  return Array.isArray(value) ? value[0] : value
}

export function sanitizeTracingHeaderValue(value: HeaderValue): string | undefined {
  if (Array.isArray(value)) {
    for (const item of value) {
      const sanitized = sanitizeTracingHeaderValue(item)
      if (sanitized !== undefined) {
        return sanitized
      }
    }
    return undefined
  }

  if (typeof value !== 'string') {
    return undefined
  }

  const sanitized = value.replace(TRACING_HEADER_CONTROL_CHARS_REGEX, '').trim()
  if (!sanitized) {
    return undefined
  }

  return sanitized.length > TRACING_HEADER_MAX_LENGTH ? sanitized.slice(0, TRACING_HEADER_MAX_LENGTH) : sanitized
}

export function getPostHogTracingHeaderValues(headers?: IncomingHttpHeaders): PostHogTracingHeaderValues {
  if (!headers) {
    return {}
  }

  const sessionId = sanitizeTracingHeaderValue(headers[POSTHOG_TRACING_HEADERS.sessionId])
  const distinctId = sanitizeTracingHeaderValue(headers[POSTHOG_TRACING_HEADERS.distinctId])

  return {
    ...(sessionId !== undefined ? { sessionId } : {}),
    ...(distinctId !== undefined ? { distinctId } : {}),
  }
}
