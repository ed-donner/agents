import type {
  PostHogCoreOptions,
  FeatureFlagValue,
  JsonType,
  PostHogFetchOptions,
  PostHogFetchResponse,
  PostHogFlagsAndPayloadsResponse,
} from '@posthog/core'
import { ContextData, ContextOptions } from './extensions/context/types'

import type { FeatureFlagEvaluations } from './feature-flag-evaluations'
import type { FlagDefinitionCacheProvider } from './extensions/feature-flags/cache'

export type IdentifyMessage = {
  distinctId: string
  properties?: Record<string | number, any>
  disableGeoip?: boolean
}

export type SendFeatureFlagsOptions = {
  onlyEvaluateLocally?: boolean
  personProperties?: Record<string, any>
  groupProperties?: Record<string, Record<string, any>>
  flagKeys?: string[]
}

export type EventMessage = Omit<IdentifyMessage, 'distinctId'> & {
  distinctId?: string // Optional - can be provided via context
  event: string
  groups?: Record<string, string | number> // Mapping of group type to group id
  /**
   * Attach feature flag values evaluated via `posthog.evaluateFlags()` to this event.
   * Prefer this over `sendFeatureFlags` — it guarantees the event carries the exact
   * values the code branched on and avoids a hidden `/flags` request on every capture.
   */
  flags?: FeatureFlagEvaluations
  /**
   * @deprecated Use the `flags` option with a `FeatureFlagEvaluations` object obtained
   * from `posthog.evaluateFlags()` instead. `sendFeatureFlags` fires a separate `/flags`
   * request on capture and may return different values than the ones the code branched on.
   */
  sendFeatureFlags?: boolean | SendFeatureFlagsOptions
  timestamp?: Date
  uuid?: string
  /**
   * Internal flag set by captureException() to indicate this $exception
   * event originated from the proper exception capture path. Used to warn users who call
   * capture() with '$exception' directly.
   */
  _originatedFromCaptureException?: boolean
}

export type GroupIdentifyMessage = {
  groupType: string
  groupKey: string // Unique identifier for the group
  properties?: Record<string | number, any>
  distinctId?: string // optional distinctId to associate message with a person
  disableGeoip?: boolean
}

export type PropertyGroup = {
  type: 'AND' | 'OR'
  values: PropertyGroup[] | FlagProperty[]
}

export type FlagProperty = {
  key: string
  type?: string
  value: FlagPropertyValue
  operator?: string
  negation?: boolean
  dependency_chain?: string[]
}

export type FlagPropertyValue = string | number | (string | number)[] | boolean

/**
 * Options for overriding feature flags.
 *
 * Supports multiple formats:
 * - `false` - Clear all overrides
 * - `string[]` - Enable a list of flags (sets them to `true`)
 * - `Record<string, FeatureFlagValue>` - Set specific flag values/variants
 * - `FeatureFlagOverrideOptions` - Set both flag values and payloads
 */
export type OverrideFeatureFlagsOptions =
  | false
  | string[]
  | Record<string, FeatureFlagValue>
  | FeatureFlagOverrideOptions

export type BaseFlagEvaluationOptions = {
  groups?: Record<string, string>
  personProperties?: Record<string, string>
  groupProperties?: Record<string, Record<string, string>>
  onlyEvaluateLocally?: boolean
  disableGeoip?: boolean
}
export type FlagEvaluationOptions = BaseFlagEvaluationOptions & {
  sendFeatureFlagEvents?: boolean
}

export type AllFlagsOptions = BaseFlagEvaluationOptions & {
  flagKeys?: string[]
}

export type FeatureFlagOverrideOptions = {
  /**
   * Flag overrides. Can be:
   * - `false` to clear flag overrides
   * - `string[]` to enable a list of flags
   * - `Record<string, FeatureFlagValue>` to set specific values/variants
   */
  flags?: false | string[] | Record<string, FeatureFlagValue>
  /**
   * Payload overrides for flags.
   * - `false` to clear payload overrides
   * - `Record<string, JsonType>` to set specific payloads
   */
  payloads?: false | Record<string, JsonType>
}

export type FeatureFlagCondition = {
  properties: FlagProperty[]
  rollout_percentage?: number
  variant?: string
  aggregation_group_type_index?: number | null
}

export type FeatureFlagBucketingIdentifier = 'distinct_id' | 'device_id' | '' | null

export type BeforeSendFn = (event: EventMessage | null) => EventMessage | null

export type PostHogOptions = Omit<PostHogCoreOptions, 'before_send'> & {
  persistence?: 'memory'
  personalApiKey?: string
  privacyMode?: boolean
  enableExceptionAutocapture?: boolean
  // The interval in milliseconds between polls for refreshing feature flag definitions. Defaults to 30 seconds.
  featureFlagsPollingInterval?: number
  // Maximum size of cache that deduplicates $feature_flag_called calls per user.
  maxCacheSize?: number
  fetch?: (url: string, options: PostHogFetchOptions) => Promise<PostHogFetchResponse>
  // Whether to enable feature flag polling for local evaluation by default. Defaults to true when personalApiKey is provided.
  // We recommend setting this to false if you are only using the personalApiKey for evaluating remote config payloads via `getRemoteConfigPayload` and not using local evaluation.
  enableLocalEvaluation?: boolean
  /**
   * Optional cache provider for feature flag definitions.
   *
   * Allows custom caching strategies (Redis, database, etc.) for flag definitions
   * in multi-worker environments. If not provided, defaults to in-memory cache.
   *
   * This enables distributed coordination where only one worker fetches flags while
   * others use cached data, reducing API calls and improving performance.
   *
   * @example
   * ```typescript
   * import type { FlagDefinitionCacheProvider } from 'posthog-node'
   *
   * class RedisCacheProvider implements FlagDefinitionCacheProvider {
   *   // ... implementation
   * }
   *
   * const client = new PostHog('api-key', {
   *   personalApiKey: 'personal-key',
   *   flagDefinitionCacheProvider: new RedisCacheProvider(redis)
   * })
   * ```
   */
  flagDefinitionCacheProvider?: FlagDefinitionCacheProvider
  /**
   * Allows modification or dropping of events before they're sent to PostHog.
   * If an array is provided, the functions are run in order.
   * If a function returns null, the event will be dropped.
   */
  before_send?: BeforeSendFn | BeforeSendFn[]
  /**
   * Evaluation contexts for feature flags.
   * When set, only feature flags that have at least one matching evaluation tag
   * will be evaluated for this SDK instance. Feature flags with no evaluation tags
   * will always be evaluated.
   *
   * Examples: ['production', 'backend', 'api']
   *
   * @default undefined
   */
  evaluationContexts?: readonly string[]
  /**
   * Evaluation environments for feature flags.
   * @deprecated Use evaluationContexts instead. This property will be removed in a future version.
   */
  evaluationEnvironments?: readonly string[]
  /**
   * Additional user agent strings to block from being tracked.
   * These are combined with the default list of blocked user agents.
   *
   * @default []
   */
  custom_blocked_useragents?: string[]
  /**
   * PREVIEW - MAY CHANGE WITHOUT WARNING - DO NOT USE IN PRODUCTION
   * Enables collection of bot traffic as $bot_pageview events instead of dropping them.
   * When enabled, events with a $raw_user_agent property that matches the bot detection list
   * will have their $pageview event renamed to $bot_pageview.
   *
   * To use this feature, pass the user agent in event properties:
   * ```ts
   * client.capture({
   *   distinctId: 'user_123',
   *   event: '$pageview',
   *   properties: {
   *     $raw_user_agent: req.headers['user-agent']
   *   }
   * })
   * ```
   */
  __preview_capture_bot_pageviews?: boolean
  /**
   * When enabled, all feature flag evaluations will use local evaluation only,
   * never falling back to server-side evaluation. This prevents unexpected server
   * requests and associated costs when using local evaluation.
   *
   * Flags that cannot be evaluated locally (e.g., those with experience continuity)
   * will return `undefined` instead of making a server request.
   *
   * @default false
   */
  strictLocalEvaluation?: boolean
  /**
   * Controls whether `FeatureFlagEvaluations` filter helpers (`onlyAccessed()` and
   * `only()`) log warnings when their input is unexpected — for example, calling
   * `onlyAccessed()` before accessing any flags, or passing unknown keys to `only()`.
   *
   * @default true
   */
  featureFlagsLogWarnings?: boolean
  /**
   * Provides the API to extend the lifetime of a serverless invocation until
   * background work (like flushing analytics events) completes after the response
   * is sent.
   *
   * @experimental Subject to change in a minor release.
   *
   * @example
   * // Vercel
   * import { waitUntil } from '@vercel/functions'
   * new PostHog('key', { waitUntil })
   */
  waitUntil?: (promise: Promise<unknown>) => void
  /**
   * Debounce interval in milliseconds for the `waitUntil`-based flush.
   * After the last event is enqueued, the SDK waits this long before flushing.
   *
   * @experimental Subject to change in a minor release.
   * @default 50
   */
  waitUntilDebounceMs?: number
  /**
   * Maximum time in milliseconds to debounce before forcing a flush.
   * Prevents starvation from rapid concurrent captures.
   *
   * @experimental Subject to change in a minor release.
   * @default 500
   */
  waitUntilMaxWaitMs?: number
  /**
   * Whether to attach the `$is_server: true` property to every captured event.
   *
   * @remarks
   * Defaults to `true` because this SDK is intended for server-side use, where
   * the property lets PostHog distinguish server events from browser and
   * react-native events. Set this to `false` when running the SDK as a
   * client/CLI so the event is attributed to the device OS normally instead of
   * being marked as a server event. When `false`, the `$is_server` property is
   * omitted entirely.
   *
   * @default true
   * @example
   * // CLI usage: don't mark events as server-side
   * new PostHog('key', { isServer: false })
   */
  isServer?: boolean
}

export type PostHogFeatureFlag = {
  id: number
  name: string
  key: string
  bucketing_identifier?: FeatureFlagBucketingIdentifier
  filters?: {
    aggregation_group_type_index?: number
    groups?: FeatureFlagCondition[]
    multivariate?: {
      variants: {
        key: string
        rollout_percentage: number
      }[]
    }
    payloads?: Record<string, string>
    // Flag-level toggle: when true, condition evaluation stops and returns false as soon as a
    // group's property filters match but the rollout percentage excludes the user, rather than
    // continuing to evaluate later groups.
    early_exit?: boolean
  }
  deleted: boolean
  active: boolean
  rollout_percentage: null | number
  ensure_experience_continuity: boolean
  experiment_set: number[]
}

/**
 * Error type constants for the $feature_flag_error property.
 *
 * These values are sent in analytics events to track flag evaluation failures.
 * They should not be changed without considering impact on existing dashboards
 * and queries that filter on these values.
 *
 * Error values:
 *   ERRORS_WHILE_COMPUTING: Server returned errorsWhileComputingFlags=true
 *   FLAG_MISSING: Requested flag not in API response
 *   QUOTA_LIMITED: Rate/quota limit exceeded
 *   UNKNOWN_ERROR: Unexpected exceptions
 */
export const FeatureFlagError = {
  ERRORS_WHILE_COMPUTING: 'errors_while_computing_flags',
  FLAG_MISSING: 'flag_missing',
  QUOTA_LIMITED: 'quota_limited',
  UNKNOWN_ERROR: 'unknown_error',
} as const

export type FeatureFlagErrorType = (typeof FeatureFlagError)[keyof typeof FeatureFlagError] | string

/**
 * Result of evaluating a feature flag, including its value and payload.
 */
export type FeatureFlagResult = {
  key: string
  enabled: boolean
  variant: string | undefined
  payload: JsonType | undefined
}

export interface IPostHog {
  /**
   * @description Capture allows you to capture anything a user does within your system,
   * which you can later use in PostHog to find patterns in usage,
   * work out which features to improve or where people are giving up.
   * A capture call requires:
   * @param distinctId which uniquely identifies your user
   * @param event We recommend using [verb] [noun], like movie played or movie updated to easily identify what your events mean later on.
   * @param properties OPTIONAL | which can be a object with any information you'd like to add
   * @param groups OPTIONAL | object of what groups are related to this event, example: { company: 'id:5' }. Can be used to analyze companies instead of users.
   * @param flags OPTIONAL | A `FeatureFlagEvaluations` snapshot from `evaluateFlags()`. Attaches those exact flag values to the event with no extra network call.
   * @param sendFeatureFlags OPTIONAL | Deprecated — prefer `flags`. Fires a hidden `/flags` request on capture to enrich the event with flag values.
   */
  capture({ distinctId, event, properties, groups, flags, sendFeatureFlags }: EventMessage): void

  /**
   * @description Capture an event immediately. Useful for edge environments where the usual queue-based sending is not preferable. Do not mix immediate and non-immediate calls.
   * @param distinctId which uniquely identifies your user
   * @param event We recommend using [verb] [noun], like movie played or movie updated to easily identify what your events mean later on.
   * @param properties OPTIONAL | which can be a object with any information you'd like to add
   * @param groups OPTIONAL | object of what groups are related to this event, example: { company: 'id:5' }. Can be used to analyze companies instead of users.
   * @param flags OPTIONAL | A `FeatureFlagEvaluations` snapshot from `evaluateFlags()`. Attaches those exact flag values to the event with no extra network call.
   * @param sendFeatureFlags OPTIONAL | Deprecated — prefer `flags`. Fires a hidden `/flags` request on capture to enrich the event with flag values.
   */
  captureImmediate({ distinctId, event, properties, groups, flags, sendFeatureFlags }: EventMessage): Promise<void>

  /**
   * @description Identify lets you add metadata on your users so you can more easily identify who they are in PostHog,
   * and even do things like segment users by these properties.
   * An identify call requires:
   * @param distinctId which uniquely identifies your user
   * @param properties with a dict with any key: value pairs
   */
  identify({ distinctId, properties }: IdentifyMessage): void

  /**
   * @description Identify lets you add metadata on your users so you can more easily identify who they are in PostHog.
   * Useful for edge environments where the usual queue-based sending is not preferable. Do not mix immediate and non-immediate calls.
   * @param distinctId which uniquely identifies your user
   * @param properties with a dict with any key: value pairs
   */
  identifyImmediate({ distinctId, properties }: IdentifyMessage): Promise<void>

  /**
   * @description To marry up whatever a user does before they sign up or log in with what they do after you need to make an alias call.
   * This will allow you to answer questions like "Which marketing channels leads to users churning after a month?"
   * or "What do users do on our website before signing up?"
   * In a purely back-end implementation, this means whenever an anonymous user does something, you'll want to send a session ID with the capture call.
   * Then, when that users signs up, you want to do an alias call with the session ID and the newly created user ID.
   * The same concept applies for when a user logs in. If you're using PostHog in the front-end and back-end,
   *  doing the identify call in the frontend will be enough.:
   * @param distinctId the current unique id
   * @param alias the unique ID of the user before
   */
  alias(data: { distinctId: string; alias: string }): void

  /**
   * @description To marry up whatever a user does before they sign up or log in with what they do after you need to make an alias call.
   * Useful for edge environments where the usual queue-based sending is not preferable. Do not mix immediate and non-immediate calls.
   * @param distinctId the current unique id
   * @param alias the unique ID of the user before
   */
  aliasImmediate(data: { distinctId: string; alias: string }): Promise<void>

  /**
   * @description PostHog feature flags (https://posthog.com/docs/features/feature-flags)
   * allow you to safely deploy and roll back new features. Once you've created a feature flag in PostHog,
   * you can use this method to check if the flag is on for a given user, allowing you to create logic to turn
   * features on and off for different user groups or individual users.
   * @param key the unique key of your feature flag
   * @param distinctId the current unique id
   * @param options: dict with optional parameters below
   * @param groups optional - what groups are currently active (group analytics). Required if the flag depends on groups.
   * @param personProperties optional - what person properties are known. Used to compute flags locally, if personalApiKey is present.
   * @param groupProperties optional - what group properties are known. Used to compute flags locally, if personalApiKey is present.
   * @param onlyEvaluateLocally optional - whether to only evaluate the flag locally. Defaults to false.
   * @param sendFeatureFlagEvents optional - whether to send feature flag events. Used for Experiments. Defaults to true.
   *
   * @returns true if the flag is on, false if the flag is off, undefined if there was an error.
   *
   * @deprecated Use {@link IPostHog.evaluateFlags} and call `flags.isEnabled(key)` on the
   *   returned snapshot. Will be removed in the next major version.
   */
  isFeatureEnabled(
    key: string,
    distinctId: string,
    options?: {
      groups?: Record<string, string>
      personProperties?: Record<string, string>
      groupProperties?: Record<string, Record<string, string>>
      onlyEvaluateLocally?: boolean
      sendFeatureFlagEvents?: boolean
    }
  ): Promise<boolean | undefined>

  /**
   * @description PostHog feature flags (https://posthog.com/docs/features/feature-flags)
   * allow you to safely deploy and roll back new features. Once you've created a feature flag in PostHog,
   * you can use this method to check if the flag is on for a given user, allowing you to create logic to turn
   * features on and off for different user groups or individual users.
   * @param key the unique key of your feature flag
   * @param distinctId the current unique id
   * @param options: dict with optional parameters below
   * @param groups optional - what groups are currently active (group analytics). Required if the flag depends on groups.
   * @param personProperties optional - what person properties are known. Used to compute flags locally, if personalApiKey is present.
   * @param groupProperties optional - what group properties are known. Used to compute flags locally, if personalApiKey is present.
   * @param onlyEvaluateLocally optional - whether to only evaluate the flag locally. Defaults to false.
   * @param sendFeatureFlagEvents optional - whether to send feature flag events. Used for Experiments. Defaults to true.
   *
   * @returns true or string(for multivariates) if the flag is on, false if the flag is off, undefined if there was an error.
   *
   * @deprecated Use {@link IPostHog.evaluateFlags} and call `flags.getFlag(key)` on the
   *   returned snapshot. Will be removed in the next major version.
   */
  getFeatureFlag(
    key: string,
    distinctId: string,
    options?: {
      groups?: Record<string, string>
      personProperties?: Record<string, string>
      groupProperties?: Record<string, Record<string, string>>
      onlyEvaluateLocally?: boolean
      sendFeatureFlagEvents?: boolean
    }
  ): Promise<FeatureFlagValue | undefined>

  /**
   * @description Retrieves payload associated with the specified flag and matched value that is passed in.
   *
   * IMPORTANT: The `matchValue` parameter should be the value you previously obtained from `getFeatureFlag()`.
   * If matchValue isn't passed (or is undefined), this method will automatically call `getFeatureFlag()`
   * internally to fetch the flag value, which could result in a network call to the PostHog server if this flag can
   * not be evaluated locally. This means that omitting `matchValue` will potentially:
   * - Bypass local evaluation
   * - Count as an additional flag evaluation against your quota
   * - Impact performance due to the extra network request
   *
   * Example usage:
   * ```js
   * const flagValue = await client.getFeatureFlag('my-flag', distinctId);
   * const payload = await client.getFeatureFlagPayload('my-flag', distinctId, flagValue);
   * ```
   *
   * @param key the unique key of your feature flag
   * @param distinctId the current unique id
   * @param matchValue The flag value previously obtained from calling `getFeatureFlag()`. Can be a string or boolean.
   *                   To avoid extra network calls, pass this parameter when you can.
   * @param options: dict with optional parameters below
   * @param onlyEvaluateLocally optional - whether to only evaluate the flag locally. Defaults to false.
   *
   * @returns payload of a json type object
   *
   * @deprecated Use {@link IPostHog.evaluateFlags} and call `flags.getFlagPayload(key)` on
   *   the returned snapshot. Will be removed in the next major version.
   */
  getFeatureFlagPayload(
    key: string,
    distinctId: string,
    matchValue?: FeatureFlagValue,
    options?: {
      onlyEvaluateLocally?: boolean
    }
  ): Promise<JsonType | undefined>

  /**
   * @description Get all feature flag values using distinctId from withContext().
   */
  getAllFlags(options?: AllFlagsOptions): Promise<Record<string, FeatureFlagValue>>

  /**
   * @description Get all feature flag values for a specific user.
   *
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to a record of flag keys and their values
   */
  getAllFlags(distinctId: string, options?: AllFlagsOptions): Promise<Record<string, FeatureFlagValue>>

  /**
   * @description Get all feature flag values and payloads using distinctId from withContext().
   */
  getAllFlagsAndPayloads(options?: AllFlagsOptions): Promise<PostHogFlagsAndPayloadsResponse>

  /**
   * @description Get all feature flag values and payloads for a specific user.
   *
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to flags and payloads
   */
  getAllFlagsAndPayloads(distinctId: string, options?: AllFlagsOptions): Promise<PostHogFlagsAndPayloadsResponse>

  /**
   * @description Get a feature flag result using distinctId from withContext().
   */
  getFeatureFlagResult(key: string, options?: FlagEvaluationOptions): Promise<FeatureFlagResult | undefined>

  /**
   * @description Get the result of evaluating a feature flag, including its value and payload.
   * This is more efficient than calling getFeatureFlag and getFeatureFlagPayload separately when you need both.
   *
   * @example
   * ```ts
   * const result = await client.getFeatureFlagResult('my-flag', 'user_123')
   * if (result) {
   *   console.log('Flag enabled:', result.enabled)
   *   console.log('Variant:', result.variant)
   *   console.log('Payload:', result.payload)
   * }
   * ```
   *
   * @param key - The feature flag key
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation
   * @returns Promise that resolves to the flag result or undefined
   */
  getFeatureFlagResult(
    key: string,
    distinctId: string,
    options?: FlagEvaluationOptions
  ): Promise<FeatureFlagResult | undefined>

  /**
   * @description Evaluate all feature flags for a user in a single call and return a
   * {@link FeatureFlagEvaluations} snapshot. Branch on `.isEnabled()` / `.getFlag()`,
   * then pass the same snapshot to `capture()` via the `flags` option so events carry
   * the exact flag values the code branched on.
   *
   * Prefer this over calling `isFeatureEnabled()` / `getFeatureFlag()` repeatedly and
   * over `capture({ sendFeatureFlags: true })` — it avoids multiple `/flags` requests
   * per incoming request.
   *
   * @example
   * ```ts
   * const flags = await posthog.evaluateFlags('user_123', { personProperties: { plan: 'enterprise' } })
   * if (flags.isEnabled('new-dashboard')) {
   *   renderNewDashboard()
   * }
   * posthog.capture({ distinctId: 'user_123', event: 'page_viewed', flags })
   * ```
   *
   * @param options - Optional configuration for flag evaluation. Pass `flagKeys` to scope the underlying `/flags` request to a subset of flags.
   */
  evaluateFlags(options?: AllFlagsOptions): Promise<FeatureFlagEvaluations>
  /**
   * @description Evaluate all feature flags for a specific user.
   *
   * @param distinctId - The user's distinct ID
   * @param options - Optional configuration for flag evaluation. Pass `flagKeys` to scope the underlying `/flags` request to a subset of flags.
   */
  evaluateFlags(distinctId: string, options?: AllFlagsOptions): Promise<FeatureFlagEvaluations>

  /**
   * @description Sets a groups properties, which allows asking questions like "Who are the most active companies"
   * using my product in PostHog.
   *
   * @param groupType Type of group (ex: 'company'). Limited to 5 per project
   * @param groupKey Unique identifier for that type of group (ex: 'id:5')
   * @param properties OPTIONAL | which can be a object with any information you'd like to add
   */
  groupIdentify({ groupType, groupKey, properties }: GroupIdentifyMessage): void

  /**
   * @description Force an immediate reload of the polled feature flags. Please note that they are
   * already polled automatically at a regular interval.
   */
  reloadFeatureFlags(): Promise<void>

  /**
   * @description Override feature flags locally. Useful for testing and local development.
   * Overridden flags take precedence over both local evaluation and remote evaluation.
   *
   * @example
   * ```ts
   * // Clear all overrides
   * posthog.overrideFeatureFlags(false)
   *
   * // Enable a list of flags (sets them to true)
   * posthog.overrideFeatureFlags(['flag-a', 'flag-b'])
   *
   * // Set specific flag values/variants
   * posthog.overrideFeatureFlags({ 'my-flag': 'variant-a', 'other-flag': true })
   *
   * // Set both flags and payloads
   * posthog.overrideFeatureFlags({
   *   flags: { 'my-flag': 'variant-a' },
   *   payloads: { 'my-flag': { discount: 20 } }
   * })
   * ```
   *
   * @param overrides - Flag overrides configuration
   */
  overrideFeatureFlags(overrides: OverrideFeatureFlagsOptions): void

  /**
   * @description Run a function with specific context that will be applied to all events captured within that context.
   * @param data Context data to apply (sessionId, distinctId, properties, enableExceptionAutocapture)
   * @param fn Function to run with the context
   * @param options Context options (fresh)
   * @returns The return value of the function
   */
  withContext<T>(data: Partial<ContextData>, fn: () => T, options?: ContextOptions): T

  /**
   * @description Set context without a callback wrapper. Must be called in the same
   * async scope that makes PostHog calls. Prefer `withContext()` when you can wrap
   * code in a callback.
   * @param data Context data to apply (distinctId, sessionId, properties)
   * @param options Context options (fresh)
   */
  enterContext(data: Partial<ContextData>, options?: ContextOptions): void

  /**
   * @description Get the current context data.
   * @returns The current context data, or undefined if no context is set
   */
  getContext(): ContextData | undefined

  /**
   * @description Flushes the events still in the queue and clears the feature flags poller to allow for
   * a clean shutdown.
   *
   * @param shutdownTimeoutMs The shutdown timeout, in milliseconds. Defaults to 30000 (30s).
   */
  shutdown(shutdownTimeoutMs?: number): void

  /**
   * @description Waits for local evaluation to be ready, with an optional timeout.
   * @param timeoutMs - Maximum time to wait in milliseconds. Defaults to 30 seconds.
   * @returns A promise that resolves to true if local evaluation is ready, false if the timeout was reached.
   */
  waitForLocalEvaluationReady(timeoutMs?: number): Promise<boolean>

  /**
   * @description Returns true if local evaluation is ready, false if it's not.
   * @returns true if local evaluation is ready, false if it's not.
   */
  isLocalEvaluationReady(): boolean
}
