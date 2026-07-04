/**
 * Deprecated experimental APIs.
 *
 * @packageDocumentation
 * @deprecated Use `import type { FlagDefinitionCacheData, FlagDefinitionCacheProvider } from 'posthog-node'` instead.
 */

const postHogNodeExperimentalDeprecationWarning =
  "[PostHog] `posthog-node/experimental` is deprecated. Use `import type { FlagDefinitionCacheData, FlagDefinitionCacheProvider } from 'posthog-node'` instead."

// eslint-disable-next-line no-console
console.warn(postHogNodeExperimentalDeprecationWarning)

export type { FlagDefinitionCacheProvider, FlagDefinitionCacheData } from './extensions/feature-flags/cache'
