import { version } from './version'

import {
  FeatureFlagValue,
  isBlockedUA,
  isPlainObject,
  JsonType,
  PostHogCaptureOptions,
  PostHogCoreStateless,
  PostHogFetchOptions,
  PostHogFetchResponse,
  PostHogFlagsAndPayloadsResponse,
  PostHogFlagsResponse,
  PostHogPersistedProperty,
} from '@posthog/core'
import {
  EventMessage,
  FeatureFlagError,
  FeatureFlagErrorType,
  FeatureFlagOverrideOptions,
  FeatureFlagResult,
  GroupIdentifyMessage,
  IdentifyMessage,
  IPostHog,
  OverrideFeatureFlagsOptions,
  PostHogOptions,
  SendFeatureFlagsOptions,
  FlagEvaluationOptions,
  AllFlagsOptions,
} from './types'
import {
  EvaluatedFlagRecord,
  FeatureFlagEvaluations,
  FeatureFlagEvaluationsHost,
  FlagCalledEventParams,
} from './feature-flag-evaluations'
import {
  FeatureFlagsPoller,
  type FeatureFlagEvaluationContext,
  RequiresServerEvaluation,
  InconclusiveMatchError,
} from './extensions/feature-flags/feature-flags'
import ErrorTracking from './extensions/error-tracking'
import { safeSetTimeout, PostHogEventProperties } from '@posthog/core'
import { PostHogMemoryStorage } from './storage-memory'
import { uuidv7 } from '@posthog/core'
import { ContextData, ContextOptions, IPostHogContext } from './extensions/context/types'

// Standard local evaluation rate limit is 600 per minute (10 per second),
// so the fastest a poller should ever be set is 100ms.
const MINIMUM_POLLING_INTERVAL = 100
const THIRTY_SECONDS = 30 * 1000
const MAX_CACHE_SIZE = 50 * 1000

const WAITUNTIL_DEBOUNCE_MS = 50
const WAITUNTIL_MAX_WAIT_MS = 500
const DEFAULT_NODE_HOST = 'https://us.i.posthog.com'

// Process-wide dedup for deprecation warnings — without this, calling a deprecated
// method in a loop would spam logs. Matches Python's `warnings.warn` default-dedup behavior.
const _emittedDeprecations = new Set<string>()

function emitDeprecationWarningOnce(id: string, message: string): void {
  if (_emittedDeprecations.has(id)) {
    return
  }
  _emittedDeprecations.add(id)
  // eslint-disable-next-line no-console
  console.warn(`[PostHog] ${message}`)
}

/**
 * @internal — clears the process-wide deprecation dedup set. Test-only.
 */
export function _resetDeprecationWarningsForTests(): void {
  _emittedDeprecations.clear()
}

function normalizeApiKey(value?: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function normalizePersonalApiKey(value?: unknown): string | undefined {
  const normalizedValue = typeof value === 'string' ? value.trim() : ''
  return normalizedValue || undefined
}

function normalizeHost(value?: unknown): string {
  const normalizedValue = typeof value === 'string' ? value.trim() : ''
  return normalizedValue || DEFAULT_NODE_HOST
}

/**
 * Derive `$feature/{key}` and `$active_feature_flags` event properties from a flat
 * `{ key: value }` map returned by the legacy `sendFeatureFlags` path.
 */
function buildFlagEventProperties(flagValues: Record<string, FeatureFlagValue> | undefined): Record<string, any> {
  if (!flagValues) {
    return {}
  }
  const additionalProperties: Record<string, any> = {}
  for (const [feature, variant] of Object.entries(flagValues)) {
    additionalProperties[`$feature/${feature}`] = variant
  }
  const activeFlags = Object.keys(flagValues)
    .filter((flag) => flagValues[flag] !== false)
    .sort()
  if (activeFlags.length > 0) {
    additionalProperties['$active_feature_flags'] = activeFlags
  }
  return additionalProperties
}

// The actual exported Nodejs API.
export abstract class PostHogBackendClient extends PostHogCoreStateless implements IPostHog {
  private _memoryStorage = new PostHogMemoryStorage()

  private featureFlagsPoller?: FeatureFlagsPoller
  protected errorTracking: ErrorTracking
  private maxCacheSize: number
  public readonly options: PostHogOptions
  protected readonly context?: IPostHogContext

  // Feature flag overrides for local testing/development
  private _flagOverrides?: Record<string, FeatureFlagValue>
  private _payloadOverrides?: Record<string, JsonType>

  distinctIdHasSentFlagCalls: Record<string, Set<string>>

  // waitUntil debounce state (per-instance)
  private _waitUntilCycle?: {
    resolve: () => void
    startedAt: number
    timer: ReturnType<typeof setTimeout> | undefined
  }

  /**
   * Initialize a new PostHog client instance.
   *
   * @example
   * ```ts
   * // Basic initialization
   * const client = new PostHogBackendClient(
   *   'your-api-key',
   *   { host: 'https://app.posthog.com' }
   * )
   * ```
   *
   * @example
   * ```ts
   * // With personal API key
   * const client = new PostHogBackendClient(
   *   'your-api-key',
   *   {
   *     host: 'https://app.posthog.com',
   *     personalApiKey: 'your-personal-api-key'
   *   }
   * )
   * ```
   *
   * {@label Initialization}
   *
   * @param apiKey - Your PostHog project API key
   * @param options - Configuration options for the client
   */
  constructor(apiKey: string, options: PostHogOptions = {}) {
    const normalizedApiKey = normalizeApiKey(apiKey)
    const normalizedOptions = {
      ...options,
      host: normalizeHost(options.host),
      personalApiKey: normalizePersonalApiKey(options.personalApiKey),
    }

    super(normalizedApiKey, normalizedOptions)

    this.options = normalizedOptions
    this.context = this.initializeContext()

    this.options.featureFlagsPollingInterval =
      typeof normalizedOptions.featureFlagsPollingInterval === 'number'
        ? Math.max(normalizedOptions.featureFlagsPollingInterval, MINIMUM_POLLING_INTERVAL)
        : THIRTY_SECONDS

    if (typeof normalizedOptions.waitUntilDebounceMs === 'number') {
      this.options.waitUntilDebounceMs = Math.max(normalizedOptions.waitUntilDebounceMs, 0)
    }
    if (typeof normalizedOptions.waitUntilMaxWaitMs === 'number') {
      this.options.waitUntilMaxWaitMs = Math.max(normalizedOptions.waitUntilMaxWaitMs, 0)
    }

    if (!this.disabled && normalizedOptions.personalApiKey) {
      if (normalizedOptions.personalApiKey.includes('phc_')) {
        throw new Error(
          'Your Personal API key is invalid. These keys are prefixed with "phx_" and can be created in PostHog project settings.'
        )
      }

      // Only start the poller if local evaluation is enabled (defaults to true for backward compatibility)
      const shouldEnableLocalEvaluation = normalizedOptions.enableLocalEvaluation !== false

      if (shouldEnableLocalEvaluation) {
        this.featureFlagsPoller = new FeatureFlagsPoller({
          pollingInterval: this.options.featureFlagsPollingInterval,
          personalApiKey: normalizedOptions.personalApiKey,
          projectApiKey: normalizedApiKey,
          timeout: normalizedOptions.requestTimeout ?? 10000, // 10 seconds
          host: this.host,
          fetch: normalizedOptions.fetch,
          onError: (err: Error) => {
            this._events.emit('error', err)
          },
          onLoad: (count: number) => {
            this._events.emit('localEvaluationFlagsLoaded', count)
          },
          customHeaders: this.getCustomHeaders(),
          cacheProvider: normalizedOptions.flagDefinitionCacheProvider,
          strictLocalEvaluation: normalizedOptions.strictLocalEvaluation,
        })
      }
    }

    this.errorTracking = new ErrorTracking(this, normalizedOptions, this._logger)
    this.distinctIdHasSentFlagCalls = {}
    this.maxCacheSize = normalizedOptions.maxCacheSize || MAX_CACHE_SIZE
  }

  protected override enqueue(type: string, message: any, options?: PostHogCaptureOptions): void {
    super.enqueue(type, message, options)
    this.scheduleDebouncedFlush()
  }

  override async flush(): Promise<void> {
    const flushPromise = super.flush()
    const waitUntil = this.options.waitUntil
    // Only register when no debounce promise is already keeping runtime alive
    if (waitUntil && !this._waitUntilCycle) {
      try {
        waitUntil(flushPromise.catch(() => {}))
      } catch {
        // waitUntil may throw outside request context
      }
    }
    return flushPromise
  }

  private scheduleDebouncedFlush(): void {
    // `waitUntil` is a serverless construct
    // if it doesn't exist, we can skip all the debounce logic and flush as normal
    const waitUntil = this.options.waitUntil
    if (!waitUntil) {
      return
    }

    if (this.disabled || this.optedOut) {
      return
    }

    if (!this._waitUntilCycle) {
      let resolve: () => void
      const promise = new Promise<void>((r) => {
        resolve = r
      })
      try {
        waitUntil(promise)
      } catch {
        // waitUntil may throw outside request context
        return
      }
      this._waitUntilCycle = { resolve: resolve!, startedAt: Date.now(), timer: undefined }
    }

    // Max time cap: if we've been debouncing too long, flush now to prevent
    // starvation from rapid concurrent captures. I.e., don't let a steady
    // stream of captures keep pushing the flush back indefinitely.
    const elapsed = Date.now() - this._waitUntilCycle.startedAt
    const maxWaitMs = this.options.waitUntilMaxWaitMs ?? WAITUNTIL_MAX_WAIT_MS
    const flushNow = elapsed >= maxWaitMs

    if (this._waitUntilCycle.timer !== undefined) {
      clearTimeout(this._waitUntilCycle.timer)
    }

    if (flushNow) {
      void this.resolveWaitUntilFlush()
      return
    }

    const debounceMs = this.options.waitUntilDebounceMs ?? WAITUNTIL_DEBOUNCE_MS
    this._waitUntilCycle.timer = safeSetTimeout(() => {
      void this.resolveWaitUntilFlush()
    }, debounceMs)
  }

  private _consumeWaitUntilCycle(): (() => void) | undefined {
    const cycle = this._waitUntilCycle
    if (cycle) {
      clearTimeout(cycle.timer)
      this._waitUntilCycle = undefined
    }
    return cycle?.resolve
  }

  private async resolveWaitUntilFlush(): Promise<void> {
    const resolve = this._consumeWaitUntilCycle()
    try {
      await super.flush()
    } catch {
      // Flush errors are already logged by flush() internals
    } finally {
      resolve?.()
    }
  }

  /**
   * Get a persisted property value from memory storage.
   *
   * @example
   * ```ts
   * // Get user ID
   * const userId = client.getPersistedProperty('userId')
   * ```
   *
   * @example
   * ```ts
   * // Get session ID
   * const sessionId = client.getPersistedProperty('sessionId')
   * ```
   *
   * {@label Initialization}
   *
   * @param key - The property key to retrieve
   * @returns The stored property value or undefined if not found
   */
  getPersistedProperty(key: PostHogPersistedProperty): any | undefined {
    return this._memoryStorage.getProperty(key)
  }

  /**
   * Set a persisted property value in memory storage.
   *
   * @example
   * ```ts
   * // Set user ID
   * client.setPersistedProperty('userId', 'user_123')
   * ```
   *
   * @example
   * ```ts
   * // Set session ID
   * client.setPersistedProperty('sessionId', 'session_456')
   * ```
   *
   * {@label Initialization}
   *
   * @param key - The property key to set
   * @param value - The value to store (null to remove)
   */
  setPersistedProperty(key: PostHogPersistedProperty, value: any | null): void {
    return this._memoryStorage.setProperty(key, value)
  }

  /**
   * Make an HTTP request using the configured fetch function or default fetch.
   *
   * @example
   * ```ts
   * // POST request
   * const response = await client.fetch('/api/endpoint', {
   *   method: 'POST',
   *   headers: { 'Content-Type': 'application/json' },
   *   body: JSON.stringify(data)
   * })
   * ```
   *
   * @internal
   *
   * {@label Initialization}
   *
   * @param url - The URL to fetch
   * @param options - Fetch options
   * @returns Promise resolving to the fetch response
   */
  fetch(url: string, options: PostHogFetchOptions): Promise<PostHogFetchResponse> {
    return this.options.fetch ? this.options.fetch(url, options) : fetch(url, options)
  }

  /**
   * Get the library version from package.json.
   *
   * @example
   * ```ts
   * // Get version
   * const version = client.getLibraryVersion()
   * console.log(`Using PostHog SDK version: ${version}`)
   * ```
   *
   * {@label Initialization}
   *
   * @returns The current library version string
   */
  getLibraryVersion(): string {
    return version
  }

  /**
   * Get the custom user agent string for this client.
   *
   * @example
   * ```ts
   * // Get user agent
   * const userAgent = client.getCustomUserAgent()
   * // Returns: "posthog-node/5.7.0"
   * ```
   *
   * {@label Identification}
   *
   * @returns The formatted user agent string
   */
  getCustomUserAgent(): string {
    return `${this.getLibraryId()}/${this.getLibraryVersion()}`
  }

  /**
   * Returns the common properties attached to every captured event.
   *
   * @remarks
   * Extends the shared core properties (`$lib`, `$lib_version`) with
   * `$is_server: true` so that events emitted from the server-side SDKs
   * (posthog-node and posthog-edge, which both extend this class) are
   * distinguishable from browser and react-native events. Browser and
   * react-native clients do not extend `PostHogBackendClient`, so they
   * never receive this property.
   *
   * This is controlled by the `isServer` option, which defaults to `true`.
   * When `isServer` is `false` (e.g. when using the SDK as a client/CLI), the
   * `$is_server` property is omitted entirely so the device OS is attributed
   * normally.
   *
   * @returns The common event properties, including `$is_server: true` when
   * the `isServer` option is enabled.
   */
  protected override getCommonEventProperties(): PostHogEventProperties {
    const commonProperties = super.getCommonEventProperties()

    if (this.options.isServer ?? true) {
      commonProperties.$is_server = true
    }

    return commonProperties
  }

  /**
   * Enable the PostHog client (opt-in).
   *
   * @example
   * ```ts
   * // Enable client
   * await client.enable()
   * // Client is now enabled and will capture events
   * ```
   *
   * {@label Privacy}
   *
   * @returns Promise that resolves when the client is enabled
   */
  enable(): Promise<void> {
    return super.optIn()
  }

  /**
   * Disable the PostHog client (opt-out).
   *
   * @example
   * ```ts
   * // Disable client
   * await client.disable()
   * // Client is now disabled and will not capture events
   * ```
   *
   * {@label Privacy}
   *
   * @returns Promise that resolves when the client is disabled
   */
  disable(): Promise<void> {
    return super.optOut()
  }

  /**
   * Enable or disable debug logging.
   *
   * @example
   * ```ts
   * // Enable debug logging
   * client.debug(true)
   * ```
   *
   * @example
   * ```ts
   * // Disable debug logging
   * client.debug(false)
   * ```
   *
   * {@label Initialization}
   *
   * @param enabled - Whether to enable debug logging
   */
  debug(enabled: boolean = true): void {
    super.debug(enabled)
    this.featureFlagsPoller?.debug(enabled)
  }

  private _warnIfInvalidCapture(
    props: EventMessage,
    stringArgumentWarning: string,
    exceptionCaptureWarning: string
  ): void {
    if (typeof props === 'string') {
      this._logger.warn(stringArgumentWarning)
    }
    if (props.event === '$exception' && !props._originatedFromCaptureException) {
      this._logger.warn(exceptionCaptureWarning)
    }
  }

  private _capturePreparedEvent(props: EventMessage, immediate: boolean): Promise<void> {
    return this.addPendingPromise(
      this.prepareEventMessage(props)
        .then(({ distinctId, event, properties, options }) => {
          const captureOptions: PostHogCaptureOptions = {
            timestamp: options.timestamp,
            disableGeoip: options.disableGeoip,
            uuid: options.uuid,
          }
          return immediate
            ? super.captureStatelessImmediate(distinctId, event, properties, captureOptions)
            : super.captureStateless(distinctId, event, properties, captureOptions)
        })
        .catch((err) => {
          if (err) {
            console.error(err)
          }
        })
    )
  }

  /**
   * Capture an event manually.
   *
   * @example
   * ```ts
   * // Basic capture
   * client.capture({
   *   distinctId: 'user_123',
   *   event: 'button_clicked',
   *   properties: { button_color: 'red' }
   * })
   * ```
   *
   * {@label Capture}
   *
   * @param props - The event properties
   * @returns void
   */
  capture(props: EventMessage): void {
    this._warnIfInvalidCapture(
      props,
      'Called capture() with a string as the first argument when an object was expected.',
      "Using `posthog.capture('$exception')` is unreliable because it does not attach required metadata. Use `posthog.captureException(error)` instead, which attaches required metadata automatically."
    )
    this._capturePreparedEvent(props, false)
  }

  /**
   * Capture an event immediately (synchronously).
   *
   * @example
   * ```ts
   * // Basic immediate capture
   * await client.captureImmediate({
   *   distinctId: 'user_123',
   *   event: 'button_clicked',
   *   properties: { button_color: 'red' }
   * })
   * ```
   *
   * @example
   * ```ts
   * // With feature flags
   * await client.captureImmediate({
   *   distinctId: 'user_123',
   *   event: 'user_action',
   *   sendFeatureFlags: true
   * })
   * ```
   *
   * @example
   * ```ts
   * // With custom feature flags options
   * await client.captureImmediate({
   *   distinctId: 'user_123',
   *   event: 'user_action',
   *   sendFeatureFlags: {
   *     onlyEvaluateLocally: true,
   *     personProperties: { plan: 'premium' },
   *     groupProperties: { org: { tier: 'enterprise' } }
   *     flagKeys: ['flag1', 'flag2']
   *   }
   * })
   * ```
   *
   * {@label Capture}
   *
   * @param props - The event properties
   * @returns Promise that resolves when the event is captured
   */
  async captureImmediate(props: EventMessage): Promise<void> {
    this._warnIfInvalidCapture(
      props,
      'Called captureImmediate() with a string as the first argument when an object was expected.',
      "Capturing a `$exception` event via `posthog.captureImmediate('$exception')` is unreliable because it does not attach required metadata. Use `posthog.captureExceptionImmediate(error)` instead, which attaches this metadata by default."
    )
    return this._capturePreparedEvent(props, true)
  }

  /**
   * Identify a user and set their properties.
   *
   * @example
   * ```ts
   * // Basic identify with properties
   * client.identify({
   *   distinctId: 'user_123',
   *   properties: {
   *     name: 'John Doe',
   *     email: 'john@example.com',
   *     plan: 'premium'
   *   }
   * })
   * ```
   *
   * @example
   * ```ts
   * // Using $set and $set_once
   * client.identify({
   *   distinctId: 'user_123',
   *   properties: {
   *     $set: { name: 'John Doe', email: 'john@example.com' },
   *     $set_once: { first_login: new Date().toISOString() }
   *     $anon_distinct_id: 'anonymous_user_456'
   *   }
   * })
   * ```
   *
   * {@label Identification}
   *
   * @param data - The identify data containing distinctId and properties
   */
  identify({ distinctId, properties = {}, disableGeoip }: IdentifyMessage): void {
    // Catch properties passed as $set and move them to the top level
    const { $set, $set_once, $anon_distinct_id, ...rest } = properties
    // if no $set is provided we assume all rest properties are $set
    const setProps = $set || rest
    const setOnceProps = $set_once || {}
    const eventProperties = {
      $set: setProps,
      $set_once: setOnceProps,
      $anon_distinct_id: $anon_distinct_id ?? undefined,
    }
    super.identifyStateless(distinctId, eventProperties, { disableGeoip })
  }

  /**
   * Identify a user and set their properties immediately (synchronously).
   *
   * @example
   * ```ts
   * // Basic immediate identify
   * await client.identifyImmediate({
   *   distinctId: 'user_123',
   *   properties: {
   *     name: 'John Doe',
   *     email: 'john@example.com'
   *   }
   * })
   * ```
   *
   * {@label Identification}
   *
   * @param data - The identify data containing distinctId and properties
   * @returns Promise that resolves when the identify is processed
   */
  async identifyImmediate({ distinctId, properties = {}, disableGeoip }: IdentifyMessage): Promise<void> {
    // Catch properties passed as $set and move them to the top level
    const { $set, $set_once, $anon_distinct_id, ...rest } = properties
    // if no $set is provided we assume all rest properties are $set
    const setProps = $set || rest
    const setOnceProps = $set_once || {}
    const eventProperties = {
      $set: setProps,
      $set_once: setOnceProps,
      $anon_distinct_id: $anon_distinct_id ?? undefined,
    }
    await super.identifyStatelessImmediate(distinctId, eventProperties, { disableGeoip })
  }

  /**
   * Create an alias to link two distinct IDs together.
   *
   * @example
   * ```ts
   * // Link an anonymous user to an identified user
   * client.alias({
   *   distinctId: 'anonymous_123',
   *   alias: 'user_456'
   * })
   * ```
   *
   * {@label Identification}
   *
   * @param data - The alias data containing distinctId and alias
   */
  alias(data: { distinctId: string; alias: string; disableGeoip?: boolean }): void {
    super.aliasStateless(data.alias, data.distinctId, undefined, { disableGeoip: data.disableGeoip })
  }

  /**
   * Create an alias to link two distinct IDs together immediately (synchronously).
   *
   * @example
   * ```ts
   * // Link an anonymous user to an identified user immediately
   * await client.aliasImmediate({
   *   distinctId: 'anonymous_123',
   *   alias: 'user_456'
   * })
   * ```
   *
   * {@label Identification}
   *
   * @param data - The alias data containing distinctId and alias
   * @returns Promise that resolves when the alias is processed
   */
  async aliasImmediate(data: { distinctId: string; alias: string; disableGeoip?: boolean }): Promise<void> {
    await super.aliasStatelessImmediate(data.alias, data.distinctId, undefined, { disableGeoip: data.disableGeoip })
  }

  /**
   * Check if local evaluation of feature flags is ready.
   *
   * @example
   * ```ts
   * // Check if ready
   * if (client.isLocalEvaluationReady()) {
   *   // Local evaluation is ready, can evaluate flags locally
   *   const flag = await client.getFeatureFlag('flag-key', 'user_123')
   * } else {
   *   // Local evaluation not ready, will use remote evaluation
   *   const flag = await client.getFeatureFlag('flag-key', 'user_123')
   * }
   * ```
   *
   * {@label Feature flags}
   *
   * @returns true if local evaluation is ready, false otherwise
   */
  isLocalEvaluationReady(): boolean {
    return this.featureFlagsPoller?.isLocalEvaluationReady() ?? false
  }

  /**
   * Wait for local evaluation of feature flags to be ready.
   *
   * @example
   * ```ts
   * // Wait for local evaluation
   * const isReady = await client.waitForLocalEvaluationReady()
   * if (isReady) {
   *   console.log('Local evaluation is ready')
   * } else {
   *   console.log('Local evaluation timed out')
   * }
   * ```
   *
   * @example
   * ```ts
   * // Wait with custom timeout
   * const isReady = await client.waitForLocalEvaluationReady(10000) // 10 seconds
   * ```
   *
   * {@label Feature flags}
   *
   * @param timeoutMs - Timeout in milliseconds (default: 30000)
   * @returns Promise that resolves to true if ready, false if timed out
   */
  async waitForLocalEvaluationReady(timeoutMs: number = THIRTY_SECONDS): Promise<boolean> {
    if (this.isLocalEvaluationReady()) {
      return true
    }

    if (this.featureFlagsPoller === undefined) {
      return false
    }

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        cleanup()
        resolve(false)
      }, timeoutMs)

      const cleanup = this._events.on('localEvaluationFlagsLoaded', (count: number) => {
        clearTimeout(timeout)
        cleanup()
        resolve(count > 0)
      })
    })
  }

  private _resolveDistinctId<T>(
    distinctIdOrOptions: string | T | undefined,
    options: T | undefined
  ): { distinctId: string | undefined; options: T | undefined } {
    if (typeof distinctIdOrOptions === 'string') {
      return { distinctId: distinctIdOrOptions, options }
    }
    return { distinctId: this.context?.get()?.distinctId, options: distinctIdOrOptions }
  }

  /**
   * Internal method that handles feature flag evaluation with full details.
   * Used by getFeatureFlag, getFeatureFlagPayload, and getFeatureFlagResult.
   *
   * @param key - The feature flag key
   * @param distinctId - The user's distinct ID
   * @param options - Evaluation options (includes sendFeatureFlagEvents, defaults to true)
   * @param matchValue - Optional match value for payload lookup (used by getFeatureFlagPayload)
   * @returns Promise that resolves to the flag result or undefined
   */
  private async _getFeatureFlagResult(
    key: string,
    distinctId: string,
    options: {
      groups?: Record<string, string>
      personProperties?: Record<string, string>
      groupProperties?: Record<string, Record<string, string>>
      onlyEvaluateLocally?: boolean
      sendFeatureFlagEvents?: boolean
      disableGeoip?: boolean
    } = {},
    matchValue?: FeatureFlagValue
  ): Promise<FeatureFlagResult | undefined> {
    if (this.disabled) {
      this._logger.warn('The client is disabled')
      return undefined
    }

    const sendFeatureFlagEvents = options.sendFeatureFlagEvents ?? true
    // Check for overrides first - they take precedence over all evaluation
    if (this._flagOverrides !== undefined && key in this._flagOverrides) {
      const overrideValue = this._flagOverrides[key]
      // undefined override simulates "flag doesn't exist"
      if (overrideValue === undefined) {
        return undefined
      }
      const overridePayload = this._payloadOverrides?.[key]
      return {
        key,
        enabled: overrideValue !== false,
        variant: typeof overrideValue === 'string' ? overrideValue : undefined,
        payload: overridePayload,
      }
    }

    const { groups, disableGeoip } = options
    let { onlyEvaluateLocally, personProperties, groupProperties } = options

    const adjustedProperties = this.addLocalPersonAndGroupProperties(
      distinctId,
      groups,
      personProperties,
      groupProperties
    )

    personProperties = adjustedProperties.allPersonProperties
    groupProperties = adjustedProperties.allGroupProperties
    const evaluationContext = this.createFeatureFlagEvaluationContext(
      distinctId,
      groups,
      personProperties,
      groupProperties
    )

    // set defaults
    if (onlyEvaluateLocally == undefined) {
      onlyEvaluateLocally = this.options.strictLocalEvaluation ?? false
    }

    let result: FeatureFlagResult | undefined = undefined
    let flagWasLocallyEvaluated = false
    let requestId: string | undefined = undefined
    let evaluatedAt: number | undefined = undefined
    let featureFlagError: FeatureFlagErrorType | undefined = undefined
    // Track metadata for event tracking (not exposed in FeatureFlagResult)
    let flagId: number | undefined = undefined
    let flagVersion: number | undefined = undefined
    let flagReason: string | undefined = undefined

    // Try local evaluation first
    const localEvaluationEnabled = this.featureFlagsPoller !== undefined
    if (localEvaluationEnabled) {
      await this.featureFlagsPoller?.loadFeatureFlags()

      const flag = this.featureFlagsPoller?.featureFlagsByKey[key]
      if (flag) {
        try {
          const localResult = await this.featureFlagsPoller?.computeFlagAndPayloadLocally(flag, evaluationContext, {
            matchValue,
          })
          if (localResult) {
            flagWasLocallyEvaluated = true
            const value = localResult.value
            flagId = flag.id
            flagReason = 'Evaluated locally'
            result = {
              key,
              enabled: value !== false,
              variant: typeof value === 'string' ? value : undefined,
              payload: localResult.payload ?? undefined,
            }
          }
        } catch (e) {
          if (e instanceof RequiresServerEvaluation || e instanceof InconclusiveMatchError) {
            // Fall through to server evaluation
            this._logger?.info(`${e.name} when computing flag locally: ${key}: ${e.message}`)
          } else {
            throw e
          }
        }
      }
    }

    // Fall back to remote evaluation if needed
    if (!flagWasLocallyEvaluated && !onlyEvaluateLocally) {
      const flagsResponse = await super.getFeatureFlagDetailsStateless(
        evaluationContext.distinctId,
        evaluationContext.groups,
        evaluationContext.personProperties,
        evaluationContext.groupProperties,
        disableGeoip,
        [key]
      )

      if (flagsResponse === undefined) {
        featureFlagError = FeatureFlagError.UNKNOWN_ERROR
      } else {
        requestId = flagsResponse.requestId
        evaluatedAt = flagsResponse.evaluatedAt

        const errors: string[] = []

        if (flagsResponse.errorsWhileComputingFlags) {
          errors.push(FeatureFlagError.ERRORS_WHILE_COMPUTING)
        }

        if (flagsResponse.quotaLimited?.includes('feature_flags')) {
          errors.push(FeatureFlagError.QUOTA_LIMITED)
        }

        const flagDetail = flagsResponse.flags[key]

        if (flagDetail === undefined) {
          errors.push(FeatureFlagError.FLAG_MISSING)
        } else {
          // Extract metadata for event tracking
          flagId = flagDetail.metadata?.id
          flagVersion = flagDetail.metadata?.version
          flagReason = flagDetail.reason?.description ?? flagDetail.reason?.code

          // Parse payload once from the API response
          let parsedPayload: JsonType | undefined = undefined
          if (flagDetail.metadata?.payload !== undefined) {
            try {
              parsedPayload = JSON.parse(flagDetail.metadata.payload)
            } catch {
              // If parsing fails, return the raw string (matches parsePayload behavior)
              parsedPayload = flagDetail.metadata.payload
            }
          }

          result = {
            key,
            enabled: flagDetail.enabled,
            variant: flagDetail.variant,
            payload: parsedPayload,
          }
        }

        if (errors.length > 0) {
          featureFlagError = errors.join(',')
        }
      }
    }

    // Send feature flag event if configured
    if (sendFeatureFlagEvents) {
      const response = result === undefined ? undefined : result.enabled === false ? false : (result.variant ?? true)
      const properties: Record<string, any> = {
        $feature_flag: key,
        $feature_flag_response: response,
        $feature_flag_id: flagId,
        $feature_flag_version: flagVersion,
        $feature_flag_reason: flagReason,
        locally_evaluated: flagWasLocallyEvaluated,
        [`$feature/${key}`]: response,
        $feature_flag_request_id: requestId,
        $feature_flag_evaluated_at: flagWasLocallyEvaluated ? Date.now() : evaluatedAt,
      }

      if (flagWasLocallyEvaluated && this.featureFlagsPoller) {
        const flagDefinitionsLoadedAt = this.featureFlagsPoller.getFlagDefinitionsLoadedAt()
        if (flagDefinitionsLoadedAt !== undefined) {
          properties.$feature_flag_definitions_loaded_at = flagDefinitionsLoadedAt
        }
      }

      if (featureFlagError) {
        properties.$feature_flag_error = featureFlagError
      }

      this._captureFlagCalledEventIfNeeded({
        distinctId,
        key,
        response,
        groups,
        disableGeoip,
        properties,
      })
    }

    // Apply payload override if present (even when there's no flag override)
    // This ensures consistency with getFeatureFlagPayload behavior
    if (result !== undefined && this._payloadOverrides !== undefined && key in this._payloadOverrides) {
      result = {
        ...result,
        payload: this._payloadOverrides[key],
      }
    }

    return result
  }

  /**
   * Get the value of a feature flag for a specific user.
   *
   * @example
   * ```ts
   * // Basic feature flag check
   * const flagValue = await client.getFeatureFlag('new-feature', 'user_123')
   * if (flagValue === 'variant-a') {
   *   // Show variant A
   * } else if (flagValue === 'variant-b') {
   *   // Show variant B
   * } else {
   *   // Flag is disabled or not found
   * }
   * ```
   *
   * @example
   * ```ts
   * // With groups and properties
   * const flagValue = await client.getFeatureFlag('org-feature', 'user_123', {
   *   groups: { organization: 'acme-corp' },
   *   personProperties: { plan: 'enterprise' },
   *   groupProperties: { organization: { tier: 'premium' } }
   * })
   * ```
   *
   * @example
   * ```ts
   * // Only evaluate locally
   * const flagValue = await client.getFeatureFlag('local-flag', 'user_123', {
   *   onlyEvaluateLocally: true
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @deprecated Use {@link evaluateFlags} and call `flags.getFlag(key)` on the returned snapshot.
   *   This consolidates flag evaluation into a single `/flags` request per incoming request and
   *   avoids drift between the values your code branched on and the values attached to events.
   *   Will be removed in the next major version.
   *
   * @param key - The feature flag key
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to the flag value or undefined
   */
  async getFeatureFlag(
    key: string,
    distinctId: string,
    options?: {
      groups?: Record<string, string>
      personProperties?: Record<string, string>
      groupProperties?: Record<string, Record<string, string>>
      onlyEvaluateLocally?: boolean
      sendFeatureFlagEvents?: boolean
      disableGeoip?: boolean
    }
  ): Promise<FeatureFlagValue | undefined> {
    emitDeprecationWarningOnce(
      'getFeatureFlag',
      '`getFeatureFlag` is deprecated and will be removed in a future major version. ' +
        'Use `posthog.evaluateFlags(distinctId, ...)` and call `flags.getFlag(key)` instead — ' +
        'this consolidates flag evaluation into a single `/flags` request per incoming request.'
    )
    const result = await this._getFeatureFlagResult(key, distinctId, {
      ...options,
      sendFeatureFlagEvents: options?.sendFeatureFlagEvents ?? this.options.sendFeatureFlagEvent ?? true,
    })
    if (result === undefined) {
      return undefined
    }
    if (result.enabled === false) {
      return false
    }
    return result.variant ?? true
  }

  /**
   * Get the payload for a feature flag.
   *
   * @example
   * ```ts
   * // Get payload for a feature flag
   * const payload = await client.getFeatureFlagPayload('flag-key', 'user_123')
   * if (payload) {
   *   console.log('Flag payload:', payload)
   * }
   * ```
   *
   * @example
   * ```ts
   * // Get payload with specific match value
   * const payload = await client.getFeatureFlagPayload('flag-key', 'user_123', 'variant-a')
   * ```
   *
   * @example
   * ```ts
   * // With groups and properties
   * const payload = await client.getFeatureFlagPayload('org-flag', 'user_123', undefined, {
   *   groups: { organization: 'acme-corp' },
   *   personProperties: { plan: 'enterprise' }
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @deprecated Use {@link evaluateFlags} and call `flags.getFlagPayload(key)` on the returned
   *   snapshot. This consolidates flag evaluation into a single `/flags` request per incoming
   *   request. Will be removed in the next major version.
   *
   * @param key - The feature flag key
   * @param distinctId - The user's distinct ID
   * @param matchValue - Optional match value to get payload for
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to the flag payload or undefined
   */
  async getFeatureFlagPayload(
    key: string,
    distinctId: string,
    matchValue?: FeatureFlagValue,
    options?: {
      groups?: Record<string, string>
      personProperties?: Record<string, string>
      groupProperties?: Record<string, Record<string, string>>
      onlyEvaluateLocally?: boolean
      /** @deprecated THIS OPTION HAS NO EFFECT, kept here for backwards compatibility reasons. */
      sendFeatureFlagEvents?: boolean
      disableGeoip?: boolean
    }
  ): Promise<JsonType | undefined> {
    emitDeprecationWarningOnce(
      'getFeatureFlagPayload',
      '`getFeatureFlagPayload` is deprecated and will be removed in a future major version. ' +
        'Use `posthog.evaluateFlags(distinctId, ...)` and call `flags.getFlagPayload(key)` instead — ' +
        'this consolidates flag evaluation into a single `/flags` request per incoming request.'
    )
    // Check for payload overrides first - they take precedence over all evaluation
    // This is checked independently from flag overrides
    if (this._payloadOverrides !== undefined && key in this._payloadOverrides) {
      return this._payloadOverrides[key]
    }

    // sendFeatureFlagEvents is intentionally ignored for payload-only calls.
    // getFeatureFlagPayload never sends $feature_flag_called events, matching pre-refactoring behavior.
    // The option is kept in the signature for backwards compatibility (marked @deprecated above).
    const result = await this._getFeatureFlagResult(
      key,
      distinctId,
      { ...options, sendFeatureFlagEvents: false },
      matchValue
    )

    // Return undefined when API fails or flag not found
    if (result === undefined) {
      return undefined
    }

    // Return payload if available, null if flag exists but no payload
    return result.payload ?? null
  }

  /**
   * Get the result of evaluating a feature flag, including its value and payload.
   * This is more efficient than calling getFeatureFlag and getFeatureFlagPayload separately when you need both.
   *
   * @example
   * ```ts
   * // Get flag result
   * const result = await client.getFeatureFlagResult('my-flag', 'user_123')
   * if (result) {
   *   console.log('Flag enabled:', result.enabled)
   *   console.log('Variant:', result.variant)
   *   console.log('Payload:', result.payload)
   * }
   * ```
   *
   * @example
   * ```ts
   * // With groups and properties
   * const result = await client.getFeatureFlagResult('org-feature', 'user_123', {
   *   groups: { organization: 'acme-corp' },
   *   personProperties: { plan: 'enterprise' }
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @param key - The feature flag key
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to the flag result or undefined
   */
  async getFeatureFlagResult(key: string, options?: FlagEvaluationOptions): Promise<FeatureFlagResult | undefined>
  async getFeatureFlagResult(
    key: string,
    distinctId: string,
    options?: FlagEvaluationOptions
  ): Promise<FeatureFlagResult | undefined>
  async getFeatureFlagResult(
    key: string,
    distinctIdOrOptions?: string | FlagEvaluationOptions,
    options?: FlagEvaluationOptions
  ): Promise<FeatureFlagResult | undefined> {
    const { distinctId: resolvedDistinctId, options: resolvedOptions } = this._resolveDistinctId(
      distinctIdOrOptions,
      options
    )

    if (!resolvedDistinctId) {
      this._logger.warn('[PostHog] distinctId is required — pass it explicitly or use withContext()')
      return undefined
    }

    return this._getFeatureFlagResult(key, resolvedDistinctId, {
      ...resolvedOptions,
      sendFeatureFlagEvents: resolvedOptions?.sendFeatureFlagEvents ?? this.options.sendFeatureFlagEvent ?? true,
    })
  }

  /**
   * Get the remote config payload for a feature flag.
   *
   * @example
   * ```ts
   * // Get remote config payload
   * const payload = await client.getRemoteConfigPayload('flag-key')
   * if (payload) {
   *   console.log('Remote config payload:', payload)
   * }
   * ```
   *
   * {@label Feature flags}
   *
   * @param flagKey - The feature flag key
   * @returns Promise that resolves to the remote config payload or undefined
   * @throws Error if personal API key is not provided
   */
  async getRemoteConfigPayload(flagKey: string): Promise<JsonType | undefined> {
    if (this.disabled) {
      this._logger.warn('The client is disabled')
      return undefined
    }

    if (!this.options.personalApiKey) {
      throw new Error('Personal API key is required for remote config payload decryption')
    }

    const response = await this._requestRemoteConfigPayload(flagKey)
    if (!response) {
      return undefined
    }

    const parsed = await response.json()
    // The payload from the endpoint is stored as a JSON encoded string. So when we return
    // it, it's effectively double encoded. As far as we know, we should never get single-encoded
    // JSON, but we'll be defensive here just in case.
    if (typeof parsed === 'string') {
      try {
        // If the parsed value is a string, try parsing it again to handle double-encoded JSON
        return JSON.parse(parsed)
      } catch (e) {
        // If second parse fails, return the string as is
        return parsed
      }
    }
    return parsed
  }

  /**
   * Check if a feature flag is enabled for a specific user.
   *
   * @example
   * ```ts
   * // Basic feature flag check
   * const isEnabled = await client.isFeatureEnabled('new-feature', 'user_123')
   * if (isEnabled) {
   *   // Feature is enabled
   *   console.log('New feature is active')
   * } else {
   *   // Feature is disabled
   *   console.log('New feature is not active')
   * }
   * ```
   *
   * @example
   * ```ts
   * // With groups and properties
   * const isEnabled = await client.isFeatureEnabled('org-feature', 'user_123', {
   *   groups: { organization: 'acme-corp' },
   *   personProperties: { plan: 'enterprise' }
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @deprecated Use {@link evaluateFlags} and call `flags.isEnabled(key)` on the returned snapshot.
   *   This consolidates flag evaluation into a single `/flags` request per incoming request.
   *   Will be removed in the next major version.
   *
   * @param key - The feature flag key
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to true if enabled, false if disabled, undefined if not found
   */
  async isFeatureEnabled(
    key: string,
    distinctId: string,
    options?: {
      groups?: Record<string, string>
      personProperties?: Record<string, string>
      groupProperties?: Record<string, Record<string, string>>
      onlyEvaluateLocally?: boolean
      sendFeatureFlagEvents?: boolean
      disableGeoip?: boolean
    }
  ): Promise<boolean | undefined> {
    emitDeprecationWarningOnce(
      'isFeatureEnabled',
      '`isFeatureEnabled` is deprecated and will be removed in a future major version. ' +
        'Use `posthog.evaluateFlags(distinctId, ...)` and call `flags.isEnabled(key)` instead — ' +
        'this consolidates flag evaluation into a single `/flags` request per incoming request.'
    )
    // Bypass the public `getFeatureFlag` so the user only sees one deprecation warning per call.
    const result = await this._getFeatureFlagResult(key, distinctId, {
      ...options,
      sendFeatureFlagEvents: options?.sendFeatureFlagEvents ?? this.options.sendFeatureFlagEvent ?? true,
    })
    if (result === undefined) {
      return undefined
    }
    if (result.enabled === false) {
      return false
    }
    const feat: FeatureFlagValue = result.variant ?? true
    return !!feat || false
  }

  /**
   * Get all feature flag values for a specific user.
   *
   * @example
   * ```ts
   * // Get all flags for a user
   * const allFlags = await client.getAllFlags('user_123')
   * console.log('User flags:', allFlags)
   * // Output: { 'flag-1': 'variant-a', 'flag-2': false, 'flag-3': 'variant-b' }
   * ```
   *
   * @example
   * ```ts
   * // With specific flag keys
   * const specificFlags = await client.getAllFlags('user_123', {
   *   flagKeys: ['flag-1', 'flag-2']
   * })
   * ```
   *
   * @example
   * ```ts
   * // With groups and properties
   * const orgFlags = await client.getAllFlags('user_123', {
   *   groups: { organization: 'acme-corp' },
   *   personProperties: { plan: 'enterprise' }
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to a record of flag keys and their values
   */
  async getAllFlags(options?: AllFlagsOptions): Promise<Record<string, FeatureFlagValue>>
  async getAllFlags(distinctId: string, options?: AllFlagsOptions): Promise<Record<string, FeatureFlagValue>>
  async getAllFlags(
    distinctIdOrOptions?: string | AllFlagsOptions,
    options?: AllFlagsOptions
  ): Promise<Record<string, FeatureFlagValue>> {
    const { distinctId: resolvedDistinctId, options: resolvedOptions } = this._resolveDistinctId(
      distinctIdOrOptions,
      options
    )
    if (!resolvedDistinctId) {
      this._logger.warn(
        '[PostHog] distinctId is required to get feature flags — pass it explicitly or use withContext()'
      )
      return {}
    }

    const response = await this.getAllFlagsAndPayloads(resolvedDistinctId, resolvedOptions)
    return response.featureFlags || {}
  }

  /**
   * Get all feature flag values and payloads for a specific user.
   *
   * @example
   * ```ts
   * // Get all flags and payloads for a user
   * const result = await client.getAllFlagsAndPayloads('user_123')
   * console.log('Flags:', result.featureFlags)
   * console.log('Payloads:', result.featureFlagPayloads)
   * ```
   *
   * @example
   * ```ts
   * // With specific flag keys
   * const result = await client.getAllFlagsAndPayloads('user_123', {
   *   flagKeys: ['flag-1', 'flag-2']
   * })
   * ```
   *
   * @example
   * ```ts
   * // Only evaluate locally
   * const result = await client.getAllFlagsAndPayloads('user_123', {
   *   onlyEvaluateLocally: true
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to flags and payloads
   */
  async getAllFlagsAndPayloads(options?: AllFlagsOptions): Promise<PostHogFlagsAndPayloadsResponse>
  async getAllFlagsAndPayloads(distinctId: string, options?: AllFlagsOptions): Promise<PostHogFlagsAndPayloadsResponse>
  async getAllFlagsAndPayloads(
    distinctIdOrOptions?: string | AllFlagsOptions,
    options?: AllFlagsOptions
  ): Promise<PostHogFlagsAndPayloadsResponse> {
    const { distinctId: resolvedDistinctId, options: resolvedOptions } = this._resolveDistinctId(
      distinctIdOrOptions,
      options
    )
    if (!resolvedDistinctId) {
      this._logger.warn(
        '[PostHog] distinctId is required to get feature flags and payloads — pass it explicitly or use withContext()'
      )
      return { featureFlags: {}, featureFlagPayloads: {} }
    }

    if (this.disabled) {
      this._logger.warn('The client is disabled')
      return { featureFlags: {}, featureFlagPayloads: {} }
    }

    const { groups, disableGeoip, flagKeys } = resolvedOptions || {}
    let { onlyEvaluateLocally, personProperties, groupProperties } = resolvedOptions || {}

    const adjustedProperties = this.addLocalPersonAndGroupProperties(
      resolvedDistinctId,
      groups,
      personProperties,
      groupProperties
    )

    personProperties = adjustedProperties.allPersonProperties
    groupProperties = adjustedProperties.allGroupProperties
    const evaluationContext = this.createFeatureFlagEvaluationContext(
      resolvedDistinctId,
      groups,
      personProperties,
      groupProperties
    )

    // set defaults
    if (onlyEvaluateLocally == undefined) {
      onlyEvaluateLocally = this.options.strictLocalEvaluation ?? false
    }

    const localEvaluationResult = await this.featureFlagsPoller?.getAllFlagsAndPayloads(evaluationContext, flagKeys)

    let featureFlags = {}
    let featureFlagPayloads = {}
    let fallbackToFlags = true
    if (localEvaluationResult) {
      featureFlags = localEvaluationResult.response
      featureFlagPayloads = localEvaluationResult.payloads
      fallbackToFlags = localEvaluationResult.fallbackToFlags
    }

    if (fallbackToFlags && !onlyEvaluateLocally) {
      const remoteEvaluationResult = await super.getFeatureFlagsAndPayloadsStateless(
        evaluationContext.distinctId,
        evaluationContext.groups,
        evaluationContext.personProperties,
        evaluationContext.groupProperties,
        disableGeoip,
        flagKeys
      )
      featureFlags = {
        ...featureFlags,
        ...(remoteEvaluationResult.flags || {}),
      }
      featureFlagPayloads = {
        ...featureFlagPayloads,
        ...(remoteEvaluationResult.payloads || {}),
      }
    }

    // Apply overrides last - they take precedence over all evaluation
    if (this._flagOverrides !== undefined) {
      featureFlags = {
        ...featureFlags,
        ...this._flagOverrides,
      }
    }
    if (this._payloadOverrides !== undefined) {
      featureFlagPayloads = {
        ...featureFlagPayloads,
        ...this._payloadOverrides,
      }
    }

    return { featureFlags, featureFlagPayloads }
  }

  /**
   * Evaluate all feature flags for a user in a single call and return a
   * {@link FeatureFlagEvaluations} snapshot. Branch on `.isEnabled()` / `.getFlag()`,
   * then pass the same snapshot to `capture()` via the `flags` option so the
   * captured event carries the exact flag values the code branched on.
   *
   * Prefer this over repeated `isFeatureEnabled()` / `getFeatureFlag()` calls and
   * over `capture({ sendFeatureFlags: true })` — it consolidates flag evaluation
   * into a single `/flags` request per incoming request.
   *
   * **Local evaluation is transparent.** When the poller can resolve a flag from
   * cached definitions, no network call is made and the snapshot's `$feature_flag_called`
   * events are tagged `locally_evaluated: true`.
   *
   * **Trim the request.** Pass `flagKeys` to scope the underlying `/flags` request
   * to a subset of flags — useful when you only need a few flags and want to reduce
   * the response payload.
   *
   * **Trim the event payload.** Use `flags.only([...])` or `flags.onlyAccessed()`
   * to filter which flags get attached to a captured event without re-fetching.
   *
   * @example
   * Basic usage:
   * ```ts
   * const flags = await client.evaluateFlags('user_123', {
   *   personProperties: { plan: 'enterprise' },
   * })
   * if (flags.isEnabled('new-dashboard')) {
   *   renderNewDashboard()
   * }
   * client.capture({ distinctId: 'user_123', event: 'page_viewed', flags })
   * ```
   *
   * @example
   * Scope the `/flags` request to specific keys:
   * ```ts
   * const flags = await client.evaluateFlags('user_123', {
   *   flagKeys: ['new-dashboard', 'checkout-flow'],
   *   personProperties: { plan: 'enterprise' },
   * })
   * ```
   *
   * @example
   * Attach only the flags the developer actually checked:
   * ```ts
   * const flags = await client.evaluateFlags('user_123')
   * if (flags.isEnabled('new-dashboard')) { ... }
   * client.capture({ distinctId: 'user_123', event: 'page_viewed', flags: flags.onlyAccessed() })
   * ```
   *
   * @example
   * Use `withContext()` to avoid repeating the distinctId:
   * ```ts
   * await client.withContext({ distinctId: 'user_123' }, async () => {
   *   const flags = await client.evaluateFlags()
   *   if (flags.isEnabled('new-dashboard')) { ... }
   *   client.capture({ event: 'page_viewed', flags })
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @param distinctIdOrOptions - The user's distinct ID, or options when the distinctId comes from `withContext()`
   * @param options - Optional configuration for flag evaluation. Supports the same fields as `getAllFlags()`, including `flagKeys` to scope the `/flags` request.
   * @returns Promise that resolves to a `FeatureFlagEvaluations` snapshot
   */
  async evaluateFlags(options?: AllFlagsOptions): Promise<FeatureFlagEvaluations>
  async evaluateFlags(distinctId: string, options?: AllFlagsOptions): Promise<FeatureFlagEvaluations>
  async evaluateFlags(
    distinctIdOrOptions?: string | AllFlagsOptions,
    options?: AllFlagsOptions
  ): Promise<FeatureFlagEvaluations> {
    const { distinctId: resolvedDistinctId, options: resolvedOptions } = this._resolveDistinctId(
      distinctIdOrOptions,
      options
    )

    if (!resolvedDistinctId) {
      this._logger.warn(
        '[PostHog] distinctId is required to evaluate feature flags — pass it explicitly or use withContext()'
      )
      return new FeatureFlagEvaluations({
        host: this._getFeatureFlagEvaluationsHost(),
        distinctId: '',
        flags: {},
      })
    }

    if (this.disabled) {
      this._logger.warn('The client is disabled')
      return new FeatureFlagEvaluations({
        host: this._getFeatureFlagEvaluationsHost(),
        distinctId: resolvedDistinctId,
        flags: {},
      })
    }

    const { groups, disableGeoip, flagKeys } = resolvedOptions || {}
    let { onlyEvaluateLocally, personProperties, groupProperties } = resolvedOptions || {}

    const adjustedProperties = this.addLocalPersonAndGroupProperties(
      resolvedDistinctId,
      groups,
      personProperties,
      groupProperties
    )
    personProperties = adjustedProperties.allPersonProperties
    groupProperties = adjustedProperties.allGroupProperties
    const evaluationContext = this.createFeatureFlagEvaluationContext(
      resolvedDistinctId,
      groups,
      personProperties,
      groupProperties
    )

    if (onlyEvaluateLocally == undefined) {
      onlyEvaluateLocally = this.options.strictLocalEvaluation ?? false
    }

    const records: Record<string, EvaluatedFlagRecord> = {}
    let requestId: string | undefined = undefined
    let evaluatedAt: number | undefined = undefined
    let errorsWhileComputing = false
    let quotaLimited = false

    // Try local evaluation first and decorate each flag with metadata from the poller.
    // `flagKeys` scopes the evaluation to a subset of definitions when provided.
    const localResult = await this.featureFlagsPoller?.getAllFlagsAndPayloads(evaluationContext, flagKeys)
    const locallyEvaluatedKeys = new Set<string>()
    if (localResult) {
      for (const [key, value] of Object.entries(localResult.response)) {
        const flagDef = this.featureFlagsPoller?.featureFlagsByKey[key]
        records[key] = {
          key,
          enabled: value !== false,
          variant: typeof value === 'string' ? value : undefined,
          payload: localResult.payloads[key],
          id: flagDef?.id,
          // The local-evaluation flag definition (`PostHogFeatureFlag`) does not carry a
          // version field; only the remote `/flags` response does via `metadata.version`.
          version: undefined,
          reason: 'Evaluated locally',
          locallyEvaluated: true,
        }
        locallyEvaluatedKeys.add(key)
      }
    }

    // Fall back to remote evaluation for any flags the poller couldn't resolve locally.
    // We use the detail-shaped endpoint so the resulting records carry id/version/reason
    // and fired $feature_flag_called events match what isFeatureEnabled()/getFeatureFlag() emit.
    const fallbackToFlags = localResult ? localResult.fallbackToFlags : true
    if (fallbackToFlags && !onlyEvaluateLocally) {
      const details = await super.getFeatureFlagDetailsStateless(
        evaluationContext.distinctId,
        evaluationContext.groups,
        evaluationContext.personProperties,
        evaluationContext.groupProperties,
        disableGeoip,
        flagKeys
      )
      if (details) {
        requestId = details.requestId
        evaluatedAt = details.evaluatedAt
        errorsWhileComputing = Boolean((details as any).errorsWhileComputingFlags)
        quotaLimited = Array.isArray(details.quotaLimited) && details.quotaLimited.includes('feature_flags')
        for (const [key, detail] of Object.entries(details.flags)) {
          if (locallyEvaluatedKeys.has(key)) {
            continue
          }
          let parsedPayload: JsonType | undefined = undefined
          if (detail.metadata?.payload !== undefined) {
            try {
              parsedPayload = JSON.parse(detail.metadata.payload)
            } catch {
              parsedPayload = detail.metadata.payload
            }
          }
          records[key] = {
            key,
            enabled: detail.enabled,
            variant: detail.variant,
            payload: parsedPayload,
            id: detail.metadata?.id,
            version: detail.metadata?.version,
            reason: detail.reason?.description ?? detail.reason?.code,
            locallyEvaluated: false,
          }
        }
      }
    }

    // Apply overrides last so they take precedence over evaluation.
    if (this._flagOverrides !== undefined) {
      for (const [key, value] of Object.entries(this._flagOverrides)) {
        if (value === undefined) {
          delete records[key]
          continue
        }
        const existing = records[key]
        records[key] = {
          key,
          enabled: value !== false,
          variant: typeof value === 'string' ? value : undefined,
          payload: existing?.payload,
          id: existing?.id,
          version: existing?.version,
          reason: existing?.reason,
          locallyEvaluated: existing?.locallyEvaluated ?? false,
        }
      }
    }
    if (this._payloadOverrides !== undefined) {
      for (const [key, payload] of Object.entries(this._payloadOverrides)) {
        const existing = records[key]
        if (existing) {
          records[key] = { ...existing, payload }
        }
      }
    }

    return new FeatureFlagEvaluations({
      host: this._getFeatureFlagEvaluationsHost(),
      distinctId: resolvedDistinctId,
      groups,
      disableGeoip,
      flags: records,
      requestId,
      evaluatedAt,
      flagDefinitionsLoadedAt: this.featureFlagsPoller?.getFlagDefinitionsLoadedAt(),
      errorsWhileComputing,
      quotaLimited,
    })
  }

  /**
   * Fires a `$feature_flag_called` event for the given flag if the (distinctId, flag, response)
   * triple hasn't already been reported for this client. Shared by the single-flag evaluation
   * path and `FeatureFlagEvaluations.isEnabled() / getFlag()` so both paths dedupe identically.
   *
   * @internal
   */
  protected _captureFlagCalledEventIfNeeded(params: FlagCalledEventParams): void {
    const { distinctId, key, response, groups, disableGeoip, properties } = params
    const groupSuffix =
      groups && Object.keys(groups).length > 0
        ? `_${JSON.stringify(Object.entries(groups).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)))}`
        : ''
    const featureFlagReportedKey = `${key}_${response}${groupSuffix}`

    if (
      distinctId in this.distinctIdHasSentFlagCalls &&
      this.distinctIdHasSentFlagCalls[distinctId].has(featureFlagReportedKey)
    ) {
      return
    }

    if (Object.keys(this.distinctIdHasSentFlagCalls).length >= this.maxCacheSize) {
      this.distinctIdHasSentFlagCalls = {}
    }
    if (this.distinctIdHasSentFlagCalls[distinctId] instanceof Set) {
      this.distinctIdHasSentFlagCalls[distinctId].add(featureFlagReportedKey)
    } else {
      this.distinctIdHasSentFlagCalls[distinctId] = new Set([featureFlagReportedKey])
    }

    this.capture({
      distinctId,
      event: '$feature_flag_called',
      properties,
      groups,
      disableGeoip,
    })
  }

  private _featureFlagEvaluationsHost?: FeatureFlagEvaluationsHost

  private _getFeatureFlagEvaluationsHost(): FeatureFlagEvaluationsHost {
    if (!this._featureFlagEvaluationsHost) {
      this._featureFlagEvaluationsHost = {
        captureFlagCalledEventIfNeeded: (params) => this._captureFlagCalledEventIfNeeded(params),
        logWarning: (message) => {
          if (this.options.featureFlagsLogWarnings !== false) {
            // These warnings guide API usage (misuse of `onlyAccessed()` / `only()`) and
            // should always surface — unlike `this._logger.warn` which is gated on debug mode.
            console.warn(`[PostHog] ${message}`)
          }
        },
      }
    }
    return this._featureFlagEvaluationsHost
  }

  /**
   * Create or update a group and its properties.
   *
   * @example
   * ```ts
   * // Create a company group
   * client.groupIdentify({
   *   groupType: 'company',
   *   groupKey: 'acme-corp',
   *   properties: {
   *     name: 'Acme Corporation',
   *     industry: 'Technology',
   *     employee_count: 500
   *   },
   *   distinctId: 'user_123'
   * })
   * ```
   *
   * @example
   * ```ts
   * // Update organization properties
   * client.groupIdentify({
   *   groupType: 'organization',
   *   groupKey: 'org-456',
   *   properties: {
   *     plan: 'enterprise',
   *     region: 'US-West'
   *   }
   * })
   * ```
   *
   * {@label Identification}
   *
   * @param data - The group identify data
   */
  groupIdentify({ groupType, groupKey, properties, distinctId, disableGeoip }: GroupIdentifyMessage): void {
    super.groupIdentifyStateless(groupType, groupKey, properties, { disableGeoip }, distinctId)
  }

  /**
   * Reload feature flag definitions from the server for local evaluation.
   *
   * @example
   * ```ts
   * // Force reload of feature flags
   * await client.reloadFeatureFlags()
   * console.log('Feature flags reloaded')
   * ```
   *
   * @example
   * ```ts
   * // Reload before checking a specific flag
   * await client.reloadFeatureFlags()
   * const flag = await client.getFeatureFlag('flag-key', 'user_123')
   * ```
   *
   * {@label Feature flags}
   *
   * @returns Promise that resolves when flags are reloaded
   */
  async reloadFeatureFlags(): Promise<void> {
    await this.featureFlagsPoller?.loadFeatureFlags(true)
  }

  /**
   * Override feature flags locally. Useful for testing and local development.
   * Overridden flags take precedence over both local evaluation and remote evaluation.
   *
   * @example
   * ```ts
   * // Clear all overrides
   * client.overrideFeatureFlags(false)
   *
   * // Enable a list of flags (sets them to true)
   * client.overrideFeatureFlags(['flag-a', 'flag-b'])
   *
   * // Set specific flag values/variants
   * client.overrideFeatureFlags({ 'my-flag': 'variant-a', 'other-flag': true })
   *
   * // Set both flags and payloads
   * client.overrideFeatureFlags({
   *   flags: { 'my-flag': 'variant-a' },
   *   payloads: { 'my-flag': { discount: 20 } }
   * })
   * ```
   *
   * {@label Feature flags}
   *
   * @param overrides - Flag overrides configuration
   */
  overrideFeatureFlags(overrides: OverrideFeatureFlagsOptions): void {
    const flagArrayToRecord = (flags: string[]) => Object.fromEntries(flags.map((f) => [f, true]))

    if (overrides === false) {
      this._flagOverrides = undefined
      this._payloadOverrides = undefined
      return
    }

    // Array syntax: ['flag-a', 'flag-b'] -> { 'flag-a': true, 'flag-b': true }
    if (Array.isArray(overrides)) {
      this._flagOverrides = flagArrayToRecord(overrides)
      return
    }

    if (this._isFeatureFlagOverrideOptions(overrides)) {
      if ('flags' in overrides) {
        if (overrides.flags === false) {
          this._flagOverrides = undefined
        } else if (Array.isArray(overrides.flags)) {
          this._flagOverrides = flagArrayToRecord(overrides.flags)
        } else if (overrides.flags !== undefined) {
          this._flagOverrides = { ...overrides.flags }
        }
      }

      if ('payloads' in overrides) {
        if (overrides.payloads === false) {
          this._payloadOverrides = undefined
        } else if (overrides.payloads !== undefined) {
          this._payloadOverrides = { ...overrides.payloads }
        }
      }

      return
    }

    // Fallback: treat as Record<string, FeatureFlagValue>
    this._flagOverrides = { ...overrides }
  }

  /**
   * Type guard to check if overrides is a FeatureFlagOverrideOptions object.
   *
   * This distinguishes between:
   * - { flags: { 'flag-a': true } } -> FeatureFlagOverrideOptions (flags is an object/array/false)
   * - { flags: true } -> Record<string, FeatureFlagValue> (a flag named "flags" with value true)
   */
  private _isFeatureFlagOverrideOptions(overrides: unknown): overrides is FeatureFlagOverrideOptions {
    if (typeof overrides !== 'object' || overrides === null || Array.isArray(overrides)) {
      return false
    }

    const obj = overrides as Record<string, unknown>

    // Check if 'flags' key exists and has a valid structure for FeatureFlagOverrideOptions
    // Valid values: false, string[], or Record<string, FeatureFlagValue> (an object)
    if ('flags' in obj) {
      const flagsValue = obj['flags']
      // If flags is false, an array, or a plain object - it's FeatureFlagOverrideOptions
      // If flags is a boolean true or a string - it's a flag named "flags" with that value
      if (
        flagsValue === false ||
        Array.isArray(flagsValue) ||
        (typeof flagsValue === 'object' && flagsValue !== null)
      ) {
        return true
      }
    }

    // Check if 'payloads' key exists and has a valid structure for FeatureFlagOverrideOptions
    // Valid values: false or Record<string, JsonType> (an object)
    if ('payloads' in obj) {
      const payloadsValue = obj['payloads']
      // If payloads is false or a plain object - it's FeatureFlagOverrideOptions
      // If payloads is a string or boolean true - it's a flag named "payloads" with that value
      if (payloadsValue === false || (typeof payloadsValue === 'object' && payloadsValue !== null)) {
        return true
      }
    }

    return false
  }

  protected abstract initializeContext(): IPostHogContext | undefined

  /**
   * Run a function with specific context that will be applied to all events captured within that context.
   * It propagates the context to all subsequent calls down the call stack.
   * Context properties like tags and sessionId will be automatically attached to all events.
   * By default, nested contexts inherit from parent contexts. Use `{ fresh: true }` to start with a clean context.
   *
   * @example
   * ```ts
   * posthog.withContext({ distinctId: 'user_123' }, () => {
   *   posthog.capture({ event: 'button clicked' })
   * })
   * ```
   *
   * {@label Context}
   *
   * @param data - Context data to apply (sessionId, distinctId, properties, enableExceptionAutocapture)
   * @param fn - Function to run with the context
   * @param options - Context options (fresh: true to start with clean context instead of inheriting)
   * @returns The return value of the function
   */
  withContext<T>(data: Partial<ContextData>, fn: () => T, options?: ContextOptions): T {
    if (!this.context) {
      // Context not supported in this environment (e.g., edge runtime)
      return fn()
    }

    return this.context.run(data, fn, options)
  }

  /**
   * Get the current context data.
   *
   * @example
   * ```ts
   * // Get current context within a withContext block
   * posthog.withContext({ distinctId: 'user_123' }, () => {
   *   const context = posthog.getContext()
   *   console.log(context?.distinctId) // 'user_123'
   * })
   * ```
   *
   * {@label Context}
   *
   * @returns The current context data, or undefined if no context is set
   */
  getContext(): ContextData | undefined {
    return this.context?.get()
  }

  /**
   * Set context without a callback wrapper.
   *
   * Uses `AsyncLocalStorage.enterWith()` to attach context to the current
   * async execution context. The context lives until that async context ends.
   *
   * Must be called in the same async scope that makes PostHog calls.
   * Calling this outside a request-scoped async context will leak context
   * across unrelated work. Prefer `withContext()` when you can wrap code
   * in a callback — it creates an isolated scope that cleans up automatically.
   *
   * @param data - Context data to apply (distinctId, sessionId, properties)
   * @param options - Context options (fresh: true to start with clean context instead of inheriting)
   */
  enterContext(data: Partial<ContextData>, options?: ContextOptions): void {
    this.context?.enter(data as ContextData, options)
  }

  /**
   * Shutdown the PostHog client gracefully.
   *
   * @example
   * ```ts
   * // Shutdown with default timeout
   * await client._shutdown()
   * ```
   *
   * @example
   * ```ts
   * // Shutdown with custom timeout
   * await client._shutdown(5000) // 5 seconds
   * ```
   *
   * {@label Shutdown}
   *
   * @param shutdownTimeoutMs - Timeout in milliseconds for shutdown
   * @returns Promise that resolves when shutdown is complete
   */
  async _shutdown(shutdownTimeoutMs?: number): Promise<void> {
    // Cancel any pending debounced flush — shutdown will flush directly.
    const resolve = this._consumeWaitUntilCycle()

    await this.featureFlagsPoller?.stopPoller(shutdownTimeoutMs)
    this.errorTracking.shutdown()
    try {
      return await super._shutdown(shutdownTimeoutMs)
    } finally {
      resolve?.()
    }
  }

  private async _requestRemoteConfigPayload(flagKey: string): Promise<PostHogFetchResponse | undefined> {
    if (this.disabled || !this.apiKey || !this.options.personalApiKey) {
      return undefined
    }

    const url = `${this.host}/api/projects/@current/feature_flags/${flagKey}/remote_config?token=${encodeURIComponent(this.apiKey)}`

    const options: PostHogFetchOptions = {
      method: 'GET',
      headers: {
        ...this.getCustomHeaders(),
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.options.personalApiKey}`,
      },
    }

    let abortTimeout = null
    if (this.options.requestTimeout && typeof this.options.requestTimeout === 'number') {
      const controller = new AbortController()
      abortTimeout = safeSetTimeout(() => {
        controller.abort()
      }, this.options.requestTimeout)
      options.signal = controller.signal
    }

    try {
      return await this.fetch(url, options)
    } catch (error) {
      this._events.emit('error', error)
      return undefined
    } finally {
      if (abortTimeout) {
        clearTimeout(abortTimeout)
      }
    }
  }

  private extractPropertiesFromEvent(
    eventProperties?: Record<string | number, any>,
    groups?: Record<string, string | number>
  ): {
    personProperties: Record<string, string>
    groupProperties: Record<string, Record<string, string>>
  } {
    if (!eventProperties) {
      return { personProperties: {}, groupProperties: {} }
    }

    const personProperties: Record<string, string> = {}
    const groupProperties: Record<string, Record<string, string>> = {}

    for (const [key, value] of Object.entries(eventProperties)) {
      // If the value is a plain object and the key exists in groups, treat it as group properties
      if (isPlainObject(value) && groups && key in groups) {
        const groupProps: Record<string, string> = {}
        for (const [groupKey, groupValue] of Object.entries(value as Record<string, any>)) {
          groupProps[String(groupKey)] = String(groupValue)
        }
        groupProperties[String(key)] = groupProps
      } else {
        // Otherwise treat as person property
        personProperties[String(key)] = String(value)
      }
    }

    return { personProperties, groupProperties }
  }

  private async getFeatureFlagsForEvent(
    distinctId: string,
    groups?: Record<string, string | number>,
    disableGeoip?: boolean,
    sendFeatureFlagsOptions?: SendFeatureFlagsOptions
  ): Promise<PostHogFlagsResponse['featureFlags'] | undefined> {
    if (this.disabled || !this.apiKey) {
      this._logger.warn('The client is disabled')
      return undefined
    }

    // Use properties directly from options if they exist
    const finalPersonProperties = sendFeatureFlagsOptions?.personProperties || {}
    const finalGroupProperties = sendFeatureFlagsOptions?.groupProperties || {}
    const flagKeys = sendFeatureFlagsOptions?.flagKeys

    // Check if we should only evaluate locally
    const onlyEvaluateLocally =
      sendFeatureFlagsOptions?.onlyEvaluateLocally ?? this.options.strictLocalEvaluation ?? false

    // If onlyEvaluateLocally is true, only use local evaluation
    if (onlyEvaluateLocally) {
      if ((this.featureFlagsPoller?.featureFlags?.length || 0) > 0) {
        const groupsWithStringValues: Record<string, string> = {}
        for (const [key, value] of Object.entries(groups || {})) {
          groupsWithStringValues[key] = String(value)
        }

        return await this.getAllFlags(distinctId, {
          groups: groupsWithStringValues,
          personProperties: finalPersonProperties,
          groupProperties: finalGroupProperties,
          disableGeoip,
          onlyEvaluateLocally: true,
          flagKeys,
        })
      } else {
        // If onlyEvaluateLocally is true but we don't have local flags, return empty
        return {}
      }
    }

    // Prefer local evaluation if available (default behavior; I'd rather not penalize users who haven't updated to the new API but still want to use local evaluation)
    if ((this.featureFlagsPoller?.featureFlags?.length || 0) > 0) {
      const groupsWithStringValues: Record<string, string> = {}
      for (const [key, value] of Object.entries(groups || {})) {
        groupsWithStringValues[key] = String(value)
      }

      return await this.getAllFlags(distinctId, {
        groups: groupsWithStringValues,
        personProperties: finalPersonProperties,
        groupProperties: finalGroupProperties,
        disableGeoip,
        onlyEvaluateLocally: true,
        flagKeys,
      })
    }

    // Fall back to remote evaluation if local evaluation is not available
    return (
      await super.getFeatureFlagsStateless(
        distinctId,
        groups,
        finalPersonProperties,
        finalGroupProperties,
        disableGeoip
      )
    ).flags
  }

  private addLocalPersonAndGroupProperties(
    distinctId: string,
    groups?: Record<string, string>,
    personProperties?: Record<string, string>,
    groupProperties?: Record<string, Record<string, string>>
  ): { allPersonProperties: Record<string, string>; allGroupProperties: Record<string, Record<string, string>> } {
    const allPersonProperties = { distinct_id: distinctId, ...(personProperties || {}) }

    const allGroupProperties: Record<string, Record<string, string>> = {}
    if (groups) {
      for (const groupName of Object.keys(groups)) {
        allGroupProperties[groupName] = {
          $group_key: groups[groupName],
          ...(groupProperties?.[groupName] || {}),
        }
      }
    }

    return { allPersonProperties, allGroupProperties }
  }

  private createFeatureFlagEvaluationContext(
    distinctId: string,
    groups?: Record<string, string>,
    personProperties?: Record<string, any>,
    groupProperties?: Record<string, Record<string, any>>
  ): FeatureFlagEvaluationContext {
    return {
      distinctId,
      groups: groups || {},
      personProperties: personProperties || {},
      groupProperties: groupProperties || {},
      evaluationCache: {},
    }
  }

  /**
   * Capture an error exception as an event.
   *
   * @example
   * ```ts
   * // Capture an error with user ID
   * try {
   *   // Some risky operation
   *   riskyOperation()
   * } catch (error) {
   *   client.captureException(error, 'user_123')
   * }
   * ```
   *
   * @example
   * ```ts
   * // Capture with additional properties
   * try {
   *   apiCall()
   * } catch (error) {
   *   client.captureException(error, 'user_123', {
   *     endpoint: '/api/users',
   *     method: 'POST',
   *     status_code: 500
   *   })
   * }
   * ```
   *
   * {@label Error tracking}
   *
   * @param error - The error to capture
   * @param distinctId - Optional user distinct ID
   * @param additionalProperties - Optional additional properties to include
   * @param uuid - Optional event UUID
   * @param flags - Optional `FeatureFlagEvaluations` snapshot to attach the same flag context as your other events
   */
  captureException(
    error: unknown,
    distinctId?: string,
    additionalProperties?: Record<string | number, any>,
    uuid?: EventMessage['uuid'],
    flags?: FeatureFlagEvaluations
  ): void {
    if (!ErrorTracking.isPreviouslyCapturedError(error)) {
      const syntheticException = new Error('PostHog syntheticException')
      this.addPendingPromise(
        ErrorTracking.buildEventMessage(
          this.getErrorPropertiesBuilder(),
          error,
          { syntheticException },
          distinctId,
          additionalProperties
        ).then((msg) => this.capture({ ...msg, uuid, flags }))
      )
    }
  }

  /**
   * Capture an error exception as an event immediately (synchronously).
   *
   * @example
   * ```ts
   * // Capture an error immediately with user ID
   * try {
   *   // Some risky operation
   *   riskyOperation()
   * } catch (error) {
   *   await client.captureExceptionImmediate(error, 'user_123')
   * }
   * ```
   *
   * @example
   * ```ts
   * // Capture with additional properties
   * try {
   *   apiCall()
   * } catch (error) {
   *   await client.captureExceptionImmediate(error, 'user_123', {
   *     endpoint: '/api/users',
   *     method: 'POST',
   *     status_code: 500
   *   })
   * }
   * ```
   *
   * {@label Error tracking}
   *
   * @param error - The error to capture
   * @param distinctId - Optional user distinct ID
   * @param additionalProperties - Optional additional properties to include
   * @param flags - Optional `FeatureFlagEvaluations` snapshot to attach the same flag context as your other events
   * @returns Promise that resolves when the error is captured
   */
  async captureExceptionImmediate(
    error: unknown,
    distinctId?: string,
    additionalProperties?: Record<string | number, any>,
    flags?: FeatureFlagEvaluations
  ): Promise<void> {
    if (!ErrorTracking.isPreviouslyCapturedError(error)) {
      const syntheticException = new Error('PostHog syntheticException')
      return this.addPendingPromise(
        ErrorTracking.buildEventMessage(
          this.getErrorPropertiesBuilder(),
          error,
          { syntheticException },
          distinctId,
          additionalProperties
        ).then((msg) => this.captureImmediate({ ...msg, flags }))
      )
    }
  }

  public async prepareEventMessage(props: EventMessage): Promise<{
    distinctId: string
    event: string
    properties: PostHogEventProperties
    options: PostHogCaptureOptions
  }> {
    const {
      distinctId,
      event,
      properties,
      groups,
      flags,
      sendFeatureFlags,
      timestamp,
      disableGeoip,
      uuid,
    }: EventMessage = props

    const contextData = this.context?.get()

    let mergedDistinctId = distinctId || contextData?.distinctId

    const mergedProperties = {
      ...this.props,
      ...(contextData?.properties || {}),
      ...(properties || {}),
    }

    if (!mergedDistinctId) {
      mergedDistinctId = uuidv7()
      mergedProperties.$process_person_profile = false
    }

    if (contextData?.sessionId && !mergedProperties.$session_id) {
      mergedProperties.$session_id = contextData.sessionId
    }

    // Run before_send if configured
    const eventMessage = this._runBeforeSend({
      distinctId: mergedDistinctId,
      event,
      properties: mergedProperties,
      groups,
      flags,
      sendFeatureFlags,
      timestamp,
      disableGeoip,
      uuid,
    })

    if (!eventMessage) {
      return Promise.reject(null)
    }

    // :TRICKY: If we flush, or need to shut down, to not lose events we want this promise to resolve before we flush
    const eventProperties = await Promise.resolve()
      .then(async () => {
        // Precedence: an explicit `flags` snapshot always wins, regardless of
        // `sendFeatureFlags`. The snapshot guarantees the event carries the same
        // values the developer branched on with no additional network call. The
        // `sendFeatureFlags` path only runs when no snapshot is provided.
        if (flags) {
          if (sendFeatureFlags) {
            console.warn(
              '[PostHog] Both `flags` and `sendFeatureFlags` were passed to capture(); using `flags` and ignoring `sendFeatureFlags`.'
            )
          }
          return flags._getEventProperties()
        }

        if (sendFeatureFlags) {
          emitDeprecationWarningOnce(
            'sendFeatureFlags',
            '`sendFeatureFlags` is deprecated and will be removed in a future major version. ' +
              'Pass a `flags` snapshot from `posthog.evaluateFlags(...)` instead — it avoids a ' +
              'second `/flags` request per capture and guarantees the event carries the exact ' +
              'flag values your code branched on.'
          )
          // If we are sending feature flags, we evaluate them locally if the user prefers it, otherwise we fall back to remote evaluation
          const sendFeatureFlagsOptions = typeof sendFeatureFlags === 'object' ? sendFeatureFlags : undefined
          const flagValues = await this.getFeatureFlagsForEvent(
            eventMessage.distinctId!,
            groups,
            disableGeoip,
            sendFeatureFlagsOptions
          )
          return buildFlagEventProperties(flagValues)
        }

        // $feature_flag_called events are not enriched with cached flags — the flags
        // on that event should reflect the specific call, not a potentially stale snapshot.
        return {}
      })
      .catch(() => {
        // Something went wrong getting the flag info - we should capture the event anyways
        return {}
      })
      .then((additionalProperties) => {
        // No matter what - capture the event
        const props = {
          ...additionalProperties,
          ...(eventMessage.properties || {}),
          $groups: eventMessage.groups || groups,
        } as PostHogEventProperties
        return props
      })

    // Handle bot pageview collection based on preview flag
    if (
      eventMessage.event === '$pageview' &&
      this.options.__preview_capture_bot_pageviews &&
      typeof eventProperties.$raw_user_agent === 'string'
    ) {
      if (isBlockedUA(eventProperties.$raw_user_agent, this.options.custom_blocked_useragents || [])) {
        eventMessage.event = '$bot_pageview'
        eventProperties.$browser_type = 'bot'
      }
    }

    return {
      distinctId: eventMessage.distinctId!,
      event: eventMessage.event,
      properties: eventProperties,
      options: {
        timestamp: eventMessage.timestamp,
        disableGeoip: eventMessage.disableGeoip,
        uuid: eventMessage.uuid,
      },
    }
  }

  private _runBeforeSend(eventMessage: EventMessage): EventMessage | null {
    const beforeSend = this.options.before_send
    if (!beforeSend) {
      return eventMessage
    }

    const fns = Array.isArray(beforeSend) ? beforeSend : [beforeSend]
    let result: EventMessage | null = eventMessage

    for (const fn of fns) {
      result = fn(result)
      if (!result) {
        this._logger.info(`Event '${eventMessage.event}' was rejected in beforeSend function`)
        return null
      }
      if (!result.properties || Object.keys(result.properties).length === 0) {
        const message = `Event '${result.event}' has no properties after beforeSend function, this is likely an error.`
        this._logger.warn(message)
      }
    }

    return result
  }
}
