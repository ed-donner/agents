import { FeatureFlagValue, JsonType } from '@posthog/core'

import { FeatureFlagError } from './types'

/**
 * Internal per-flag record stored by a {@link FeatureFlagEvaluations} instance.
 * Not part of the public API.
 *
 * @internal
 */
export type EvaluatedFlagRecord = {
  key: string
  enabled: boolean
  variant: string | undefined
  payload: JsonType | undefined
  id: number | undefined
  version: number | undefined
  reason: string | undefined
  locallyEvaluated: boolean
}

/**
 * Parameters passed to the host when a `$feature_flag_called` event should be captured.
 *
 * @internal
 */
export type FlagCalledEventParams = {
  distinctId: string
  key: string
  response: FeatureFlagValue | undefined
  groups: Record<string, string | number> | undefined
  disableGeoip: boolean | undefined
  properties: Record<string, any>
}

/**
 * Thin interface the evaluations object uses to talk back to the PostHog client.
 * Keeps the class decoupled from the full client surface area.
 *
 * @internal
 */
export interface FeatureFlagEvaluationsHost {
  captureFlagCalledEventIfNeeded(params: FlagCalledEventParams): void
  logWarning(message: string): void
}

/**
 * A snapshot of feature flag evaluations for a single distinctId at a point in time.
 *
 * Returned by {@link IPostHog.evaluateFlags} — branch on `isEnabled()` / `getFlag()`
 * and pass the same object to `capture()` via the `flags` option so the captured event
 * carries the exact flag values the code branched on.
 *
 * ```ts
 * const flags = await posthog.evaluateFlags(distinctId, { personProperties: { plan: 'enterprise' } })
 *
 * if (flags.isEnabled('new-dashboard')) {
 *   renderNewDashboard()
 * }
 *
 * posthog.capture({ distinctId, event: 'page_viewed', flags })
 * ```
 *
 * To narrow the set of flags that get attached to a captured event, use the in-memory
 * helpers `only([...])` and `onlyAccessed()`. To narrow the set of flags requested from
 * the server in the first place, pass `flagKeys` to `evaluateFlags()`.
 */
export class FeatureFlagEvaluations {
  private readonly _host: FeatureFlagEvaluationsHost
  private readonly _distinctId: string
  private readonly _groups: Record<string, string | number> | undefined
  private readonly _disableGeoip: boolean | undefined
  private readonly _flags: Record<string, EvaluatedFlagRecord>
  private readonly _requestId: string | undefined
  private readonly _evaluatedAt: number | undefined
  private readonly _flagDefinitionsLoadedAt: number | undefined
  private readonly _errorsWhileComputing: boolean
  private readonly _quotaLimited: boolean
  private readonly _accessed: Set<string>
  // True for snapshots produced by `only()` / `onlyAccessed()` — used to suppress
  // misleading `flag_missing` events when branching is performed on a filtered slice.
  private readonly _isSlice: boolean

  /**
   * @internal — instances are created by the SDK via `posthog.evaluateFlags()`.
   */
  constructor(init: {
    host: FeatureFlagEvaluationsHost
    distinctId: string
    groups?: Record<string, string | number>
    disableGeoip?: boolean
    flags: Record<string, EvaluatedFlagRecord>
    requestId?: string
    evaluatedAt?: number
    flagDefinitionsLoadedAt?: number
    errorsWhileComputing?: boolean
    quotaLimited?: boolean
    accessed?: Set<string>
    isSlice?: boolean
  }) {
    this._host = init.host
    this._distinctId = init.distinctId
    this._groups = init.groups
    this._disableGeoip = init.disableGeoip
    this._flags = init.flags
    this._requestId = init.requestId
    this._evaluatedAt = init.evaluatedAt
    this._flagDefinitionsLoadedAt = init.flagDefinitionsLoadedAt
    this._errorsWhileComputing = init.errorsWhileComputing ?? false
    this._quotaLimited = init.quotaLimited ?? false
    this._accessed = init.accessed ?? new Set()
    this._isSlice = init.isSlice ?? false
  }

  /**
   * Check whether a feature flag is enabled. Fires a `$feature_flag_called` event
   * on the first access per (distinctId, flag, value) tuple, deduped via the SDK's
   * existing cache.
   *
   * Flags that were not returned from the underlying evaluation are treated as
   * disabled (returns `false`).
   */
  isEnabled(key: string): boolean {
    const flag = this._flags[key]
    this._recordAccess(key)
    return flag?.enabled ?? false
  }

  /**
   * Get the evaluated value of a feature flag. Fires a `$feature_flag_called` event
   * on the first access per (distinctId, flag, value) tuple.
   *
   * Returns the variant string for multivariate flags, `true` for enabled flags
   * without a variant, `false` for disabled flags, and `undefined` for flags that
   * were not returned by the evaluation.
   */
  getFlag(key: string): FeatureFlagValue | undefined {
    const flag = this._flags[key]
    this._recordAccess(key)
    if (!flag) {
      return undefined
    }
    if (!flag.enabled) {
      return false
    }
    return flag.variant ?? true
  }

  /**
   * Get the payload associated with a feature flag. Does not count as an access
   * for `onlyAccessed()` and does not fire any event.
   */
  getFlagPayload(key: string): JsonType | undefined {
    return this._flags[key]?.payload
  }

  /**
   * Return a filtered copy containing only flags that have been accessed via
   * `isEnabled()` or `getFlag()` before this call.
   *
   * Order-dependent: if nothing has been accessed yet, the returned snapshot is
   * empty. The method honors its name — pre-access if you want a populated result.
   *
   * **Note:** the returned snapshot is intended for `capture()`, not for further
   * branching. Calling `isEnabled()` / `getFlag()` on it for a key that was filtered
   * out is a no-op (no event is fired) — the flag wasn't actually missing, it was
   * excluded from the slice.
   */
  onlyAccessed(): FeatureFlagEvaluations {
    const filtered: Record<string, EvaluatedFlagRecord> = {}
    for (const key of this._accessed) {
      const flag = this._flags[key]
      if (flag) {
        filtered[key] = flag
      }
    }
    return this._cloneWith(filtered)
  }

  /**
   * Return a filtered copy containing only flags with the given keys. Keys that
   * are not present in the evaluation are dropped and logged as a warning.
   *
   * **Note:** like `onlyAccessed()`, the returned snapshot is intended for `capture()`.
   * Branching on a filtered key that was excluded from the slice is a no-op.
   */
  only(keys: string[]): FeatureFlagEvaluations {
    const filtered: Record<string, EvaluatedFlagRecord> = {}
    const missing: string[] = []
    for (const key of keys) {
      const flag = this._flags[key]
      if (flag) {
        filtered[key] = flag
      } else {
        missing.push(key)
      }
    }
    if (missing.length > 0) {
      this._host.logWarning(
        `FeatureFlagEvaluations.only() was called with flag keys that are not in the evaluation set and will be dropped: ${missing.join(', ')}`
      )
    }
    return this._cloneWith(filtered)
  }

  /**
   * Returns the flag keys that are part of this evaluation.
   */
  get keys(): string[] {
    return Object.keys(this._flags)
  }

  /**
   * Build the `$feature/*` and `$active_feature_flags` event properties derived
   * from the current flag set. Called by `capture()` when an event is captured
   * with `flags: ...`.
   *
   * @internal
   */
  _getEventProperties(): Record<string, any> {
    const properties: Record<string, any> = {}
    const activeFlags: string[] = []
    for (const [key, flag] of Object.entries(this._flags)) {
      const value = flag.enabled === false ? false : (flag.variant ?? true)
      properties[`$feature/${key}`] = value
      if (flag.enabled) {
        activeFlags.push(key)
      }
    }
    if (activeFlags.length > 0) {
      activeFlags.sort()
      properties['$active_feature_flags'] = activeFlags
    }
    return properties
  }

  private _cloneWith(flags: Record<string, EvaluatedFlagRecord>): FeatureFlagEvaluations {
    return new FeatureFlagEvaluations({
      host: this._host,
      distinctId: this._distinctId,
      groups: this._groups,
      disableGeoip: this._disableGeoip,
      flags,
      requestId: this._requestId,
      evaluatedAt: this._evaluatedAt,
      flagDefinitionsLoadedAt: this._flagDefinitionsLoadedAt,
      errorsWhileComputing: this._errorsWhileComputing,
      quotaLimited: this._quotaLimited,
      // Copy the accessed set so the child can track further access independently
      // of the parent. Callers expect `onlyAccessed()` on the parent to reflect
      // only what the parent saw, not what happened on filtered views.
      accessed: new Set(this._accessed),
      isSlice: true,
    })
  }

  private _recordAccess(key: string): void {
    this._accessed.add(key)

    // Empty snapshots (no resolvable distinctId) are returned by `evaluateFlags()` as a
    // safety fallback. Firing $feature_flag_called for them would emit events with an
    // empty distinct_id, polluting analytics — short-circuit here instead.
    if (this._distinctId === '') {
      return
    }

    // On filtered slices (returned by `only()` / `onlyAccessed()`), a key absent from
    // the slice doesn't mean the flag is missing from PostHog — it was filtered out.
    // Don't fire a misleading `flag_missing` event; slices are intended for `capture()`,
    // not for further branching.
    if (this._isSlice && !(key in this._flags)) {
      return
    }

    const flag = this._flags[key]
    const response: FeatureFlagValue | undefined =
      flag === undefined ? undefined : flag.enabled === false ? false : (flag.variant ?? true)

    const properties: Record<string, any> = {
      $feature_flag: key,
      $feature_flag_response: response,
      $feature_flag_id: flag?.id,
      $feature_flag_version: flag?.version,
      $feature_flag_reason: flag?.reason,
      locally_evaluated: flag?.locallyEvaluated ?? false,
      [`$feature/${key}`]: response,
      $feature_flag_request_id: this._requestId,
      $feature_flag_evaluated_at: flag?.locallyEvaluated ? Date.now() : this._evaluatedAt,
    }

    if (flag?.locallyEvaluated && this._flagDefinitionsLoadedAt !== undefined) {
      properties.$feature_flag_definitions_loaded_at = this._flagDefinitionsLoadedAt
    }

    // Build the comma-joined `$feature_flag_error` matching the single-flag path's
    // granularity: response-level errors (errors-while-computing, quota-limited) are
    // combined with per-flag errors (flag-missing) so consumers can filter by type.
    const errors: string[] = []
    if (this._errorsWhileComputing) {
      errors.push(FeatureFlagError.ERRORS_WHILE_COMPUTING)
    }
    if (this._quotaLimited) {
      errors.push(FeatureFlagError.QUOTA_LIMITED)
    }
    if (flag === undefined) {
      errors.push(FeatureFlagError.FLAG_MISSING)
    }
    if (errors.length > 0) {
      properties.$feature_flag_error = errors.join(',')
    }

    this._host.captureFlagCalledEventIfNeeded({
      distinctId: this._distinctId,
      key,
      response,
      groups: this._groups,
      disableGeoip: this._disableGeoip,
      properties,
    })
  }
}
