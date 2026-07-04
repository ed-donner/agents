import { isArray, isNoLike } from './utils'
import { uuidv7 } from './vendor/uuidv7'

const COOKIE_PREFIX = 'ph_'
const COOKIE_SUFFIX = '_posthog'

/**
 * Minimal cookie-reading interface compatible with Next.js `cookies()`,
 * `request.cookies`, and plain objects.
 */
export interface CookieStore {
  get(name: string): { value: string } | undefined
}

/**
 * Adapts a raw `Cookie` header string into a {@link CookieStore}.
 */
export function cookieStoreFromHeader(cookieHeader: string): CookieStore {
  const cookies: Record<string, string> = {}
  if (cookieHeader) {
    for (const pair of cookieHeader.split(';')) {
      const [key, ...valueParts] = pair.trim().split('=')
      if (key) {
        const raw = valueParts.join('=').trim()
        // `decodeURIComponent` throws `URIError` on malformed sequences (e.g. `%gg`).
        // The Cookie header is externally controlled, so fall back to the raw value
        // rather than crashing the request handler.
        try {
          cookies[key.trim()] = decodeURIComponent(raw)
        } catch {
          cookies[key.trim()] = raw
        }
      }
    }
  }
  return { get: (name: string) => (name in cookies ? { value: cookies[name] } : undefined) }
}

export interface PostHogCookieState {
  distinctId: string
  isIdentified: boolean
  sessionId?: string
  deviceId?: string
}

/**
 * Returns the PostHog cookie name for the given API key.
 *
 * PostHog-js stores state in a cookie named `ph_<sanitized_token>_posthog`.
 * The token is sanitized by replacing `+` with `PL`, `/` with `SL`, `=` with `EQ`.
 *
 * @param apiKey - The PostHog project API key
 * @returns The cookie name string
 */
export function getPostHogCookieName(apiKey: string): string {
  const sanitized = apiKey.replace(/\+/g, 'PL').replace(/\//g, 'SL').replace(/=/g, 'EQ')
  return `${COOKIE_PREFIX}${sanitized}${COOKIE_SUFFIX}`
}

/**
 * Serializes an anonymous ID into the JSON format posthog-js expects.
 *
 * When `distinct_id === $device_id`, posthog-js treats the user as anonymous.
 *
 * @param anonymousId - The anonymous distinct ID to serialize
 * @returns JSON string suitable for the PostHog cookie value
 */
export function serializePostHogCookie(anonymousId: string): string {
  const now = Date.now()
  const sessionId = uuidv7()
  return JSON.stringify({
    distinct_id: anonymousId,
    $device_id: anonymousId,
    $user_state: 'anonymous',
    $sesid: [now, sessionId, now],
  })
}

/**
 * Reads and parses the PostHog cookie from a cookie store.
 *
 * Compatible with Next.js `cookies()`, `request.cookies`, and any object
 * with a `get(name)` method that returns `{ value: string } | undefined`.
 */
export function readPostHogCookie(cookies: CookieStore, apiKey: string): PostHogCookieState | null {
  const cookieName = getPostHogCookieName(apiKey)
  const cookie = cookies.get(cookieName)
  return cookie ? parsePostHogCookie(cookie.value) : null
}

/**
 * Converts cookie state into PostHog properties (e.g. `$session_id`, `$device_id`).
 */
export function cookieStateToProperties(state: PostHogCookieState | null): Record<string, string> | undefined {
  if (!state) {
    return undefined
  }
  const props: Record<string, string> = {}
  if (state.sessionId) {
    props.$session_id = state.sessionId
  }
  if (state.deviceId) {
    props.$device_id = state.deviceId
  }
  return Object.keys(props).length > 0 ? props : undefined
}

/**
 * Parses a PostHog cookie value and extracts identity information.
 *
 * The cookie value is a JSON object containing `distinct_id` and `$user_state`.
 * A user is considered identified if `$user_state` is `'identified'`.
 *
 * @param cookieValue - The raw cookie string value
 * @returns Parsed identity state, or null if the cookie is missing/invalid
 */
export function parsePostHogCookie(cookieValue: string): PostHogCookieState | null {
  if (!cookieValue) {
    return null
  }

  try {
    const parsed = JSON.parse(cookieValue)
    if (!parsed || typeof parsed !== 'object' || !parsed.distinct_id) {
      return null
    }

    // $sesid is stored as [lastActivityTimestamp, sessionId, sessionStartTimestamp]
    const sesid = isArray(parsed.$sesid) ? parsed.$sesid[1] : undefined

    return {
      distinctId: String(parsed.distinct_id),
      isIdentified: parsed.$user_state === 'identified',
      sessionId: typeof sesid === 'string' ? sesid : undefined,
      deviceId: typeof parsed.$device_id === 'string' ? parsed.$device_id : undefined,
    }
  } catch {
    return null
  }
}

export interface ConsentCookieConfig {
  consent_persistence_name?: string | null
  opt_out_capturing_cookie_prefix?: string | null
}

const CONSENT_PREFIX = '__ph_opt_in_out_'

export function getConsentCookieName(apiKey: string, config?: ConsentCookieConfig): string {
  if (config?.consent_persistence_name) {
    return config.consent_persistence_name
  }
  if (config?.opt_out_capturing_cookie_prefix) {
    return config.opt_out_capturing_cookie_prefix + apiKey
  }
  return CONSENT_PREFIX + apiKey
}

export interface ConsentConfig extends ConsentCookieConfig {
  opt_out_capturing_by_default?: boolean
}

export function isOptedOut(cookies: CookieStore, apiKey: string, config?: ConsentConfig): boolean {
  const cookieName = getConsentCookieName(apiKey, config)
  const cookie = cookies.get(cookieName)

  if (cookie) {
    return isNoLike(cookie.value)
  }

  // No consent cookie means pending — defer to config
  return config?.opt_out_capturing_by_default ?? false
}
