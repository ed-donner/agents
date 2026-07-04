import type { PostHogFeatureFlag, PropertyGroup } from '../../types'

/**
 * Represents the complete set of feature flag data needed for local evaluation.
 *
 * This includes flag definitions, group type mappings, and cohort property groups.
 */
export interface FlagDefinitionCacheData {
  /** Array of feature flag definitions */
  flags: PostHogFeatureFlag[]
  /** Mapping of group type index to group name */
  groupTypeMapping: Record<string, string>
  /** Cohort property groups for local evaluation */
  cohorts: Record<string, PropertyGroup>
}

/**
 * Provider interface for caching feature flag definitions.
 *
 * Implementations can use this to control when flag definitions are fetched
 * and how they're cached (Redis, database, filesystem, etc.).
 *
 * This interface is designed for server-side environments where multiple workers
 * need to share flag definitions and coordinate fetching to reduce API calls.
 *
 * All methods may throw errors - the poller will catch and log them gracefully,
 * ensuring cache provider errors never break flag evaluation.
 *
 * @example
 * ```typescript
 * import type { FlagDefinitionCacheData, FlagDefinitionCacheProvider } from 'posthog-node'
 *
 * class RedisFlagCache implements FlagDefinitionCacheProvider {
 *   constructor(private redis: Redis, private teamKey: string) { }
 *
 *   async getFlagDefinitions(): Promise<FlagDefinitionCacheData | undefined> {
 *     const cached = await this.redis.get(`posthog:flags:${this.teamKey}`)
 *     return cached ? JSON.parse(cached) : undefined
 *   }
 *
 *   async shouldFetchFlagDefinitions(): Promise<boolean> {
 *     // Acquire distributed lock - only one worker fetches
 *     const acquired = await this.redis.set(`posthog:flags:${this.teamKey}:lock`, '1', 'EX', 60, 'NX')
 *     return acquired === 'OK'
 *   }
 *
 *   async onFlagDefinitionsReceived(data: FlagDefinitionCacheData): Promise<void> {
 *     await this.redis.set(`posthog:flags:${this.teamKey}`, JSON.stringify(data), 'EX', 300)
 *     await this.redis.del(`posthog:flags:${this.teamKey}:lock`)
 *   }
 *
 *   async shutdown(): Promise<void> {
 *     await this.redis.del(`posthog:flags:${this.teamKey}:lock`)
 *   }
 * }
 * ```
 */
export interface FlagDefinitionCacheProvider {
  /**
   * Retrieve cached flag definitions.
   *
   * Called when the poller is refreshing in-memory flag definitions. If this returns undefined
   * (or throws an error), the poller will fetch fresh data from the PostHog API if no flag
   * definitions are in memory. Otherwise, stale cache data is used until the next poll cycle.
   *
   * @returns cached definitions if available, undefined if cache is empty
   * @throws if an error occurs while accessing the cache (error will be logged)
   */
  getFlagDefinitions(): Promise<FlagDefinitionCacheData | undefined> | FlagDefinitionCacheData | undefined

  /**
   * Determines whether this instance should fetch new flag definitions.
   *
   * Use this to implement distributed coordination (e.g., via distributed locks)
   * to ensure only one instance fetches at a time in a multi-worker setup.
   *
   * When multiple workers share a cache, typically only one should fetch while
   * others use cached data. Implementations can use Redis locks, database locks,
   * or other coordination mechanisms.
   *
   * @returns true if this instance should fetch, false to skip and read cache
   * @throws if coordination backend is unavailable (error will be logged, fetch continues)
   */
  shouldFetchFlagDefinitions(): Promise<boolean> | boolean

  /**
   * Called after successfully receiving new flag definitions from PostHog.
   *
   * Store the definitions in your cache backend here. This is called only
   * after a successful API response with valid flag data.
   *
   * If this method throws, the error is logged but flag definitions are still
   * stored in memory, ensuring local evaluation can still be performed.
   *
   * @param data - The complete flag definition data from PostHog
   * @throws if storage backend is unavailable (error will be logged)
   */
  onFlagDefinitionsReceived(data: FlagDefinitionCacheData): Promise<void> | void

  /**
   * Called when the PostHog client shuts down.
   *
   * Release any held locks, close connections, or clean up resources here.
   *
   * Both sync and async cleanup are supported. Async cleanup has a timeout
   * (default 30s, configurable via client shutdown options) to prevent the
   * process shutdown from hanging indefinitely.
   *
   * @returns Promise that resolves when cleanup is complete, or void for sync cleanup
   */
  shutdown(): Promise<void> | void
}
