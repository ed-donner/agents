import { isFunction } from './utils/type-utils'

const DISTINCT_ID_HEADER = 'X-POSTHOG-DISTINCT-ID'
const SESSION_ID_HEADER = 'X-POSTHOG-SESSION-ID'
const PATCH_MARKER = '__posthog_tracing_headers_patched__'

const parseHostname = (url: string): string | undefined => {
  try {
    return new URL(url).hostname
  } catch {
    return undefined
  }
}

const shouldAddHeaders = (url: string, hostnames: string[]): boolean => {
  const hostname = parseHostname(url)
  if (!hostname) {
    return false
  }
  return hostnames.includes(hostname)
}

/**
 * Minimal contract the tracing-headers patch needs from a PostHog client:
 * something that can report the current distinct and session ids.
 */
export interface TracingHeadersClient {
  getDistinctId(): string
  getSessionId(): string
}

type FetchFn = typeof fetch
type PatchedFetch = FetchFn & { [PATCH_MARKER]?: { original: FetchFn } }

/**
 * Patches `globalThis.fetch` to inject `X-POSTHOG-DISTINCT-ID` and
 * `X-POSTHOG-SESSION-ID` headers on requests whose hostname matches `hostnames`.
 *
 * Used by SDKs that run in environments with a WHATWG `fetch` (posthog-react-native,
 * posthog-web) to link outgoing requests to the PostHog session — e.g. to link LLM
 * traces captured by a backend to a frontend session replay.
 *
 * The wrapped fetch is tagged with a non-enumerable marker so that calling this
 * again (on HMR, tests, or a second PostHog instance) unwraps the previous patch
 * before rewrapping — preventing patches from stacking. Returns a function that
 * restores the original fetch when called.
 */
export const patchFetchForTracingHeaders = (client: TracingHeadersClient, hostnames: string[]): (() => void) => {
  const globalAny = globalThis as unknown as { fetch?: PatchedFetch }
  const currentFetch = globalAny.fetch
  if (!isFunction(currentFetch)) {
    return () => {}
  }

  // If we already patched fetch ourselves, unwrap so the latest client's hostname list
  // and session/distinct ids take effect without stacking patches.
  //
  // Limitation: we only unwrap our own immediate predecessor. If another library wraps fetch
  // between two patch calls, their wrapper has no PATCH_MARKER, so we treat it as the original —
  // meaning the earlier patch stays live underneath and headers could be written twice.
  // This is considered out of scope; we rely on PostHog being initialised once per app.
  const originalFetch: FetchFn = currentFetch[PATCH_MARKER]?.original ?? currentFetch

  const wrappedFetch: PatchedFetch = async function (input, init) {
    try {
      const urlString =
        typeof input === 'string'
          ? input
          : input instanceof URL
            ? input.toString()
            : input instanceof Request
              ? input.url
              : undefined
      if (urlString && shouldAddHeaders(urlString, hostnames)) {
        const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined))
        const distinctId = client.getDistinctId()
        const sessionId = client.getSessionId()
        if (distinctId) {
          headers.set(DISTINCT_ID_HEADER, distinctId)
        }
        if (sessionId) {
          headers.set(SESSION_ID_HEADER, sessionId)
        }
        const initWithHeaders = { ...(init ?? {}), headers }
        return originalFetch.call(globalAny, input, initWithHeaders)
      }
    } catch {
      // If anything goes wrong, fall through to the original fetch without tracing headers.
    }
    return originalFetch.call(globalAny, input, init)
  }

  Object.defineProperty(wrappedFetch, PATCH_MARKER, {
    value: { original: originalFetch },
    enumerable: false,
  })

  globalAny.fetch = wrappedFetch

  return () => {
    if (globalAny.fetch === wrappedFetch) {
      globalAny.fetch = originalFetch
    }
  }
}
