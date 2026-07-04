// Re-export OTLP/log types from @posthog/types so the rest of the logs module can
// pull everything from one place.
export type {
  LogSeverityLevel,
  OtlpSeverityText,
  OtlpSeverityEntry,
  LogAttributeValue,
  LogAttributes,
  CaptureLogOptions,
  OtlpAnyValue,
  OtlpKeyValue,
  OtlpLogRecord,
  OtlpLogsPayload,
} from '@posthog/types'

/**
 * SDK-internal context the host SDK passes to `buildOtlpLogRecord` at capture
 * time. Each SDK populates the fields that apply to it: browser fills
 * `currentUrl`, mobile fills `screenName` / `appState`. Missing fields are
 * omitted from the OTLP record (no stray attributes).
 *
 * Internal to `@posthog/core` — customers don't see this in autocomplete.
 */
export interface LogSdkContext {
  distinctId?: string
  sessionId?: string
  /** Web-only — current page URL */
  currentUrl?: string
  /** Mobile-only — current screen / view name */
  screenName?: string
  /** Mobile-only — app foreground/background state at capture time */
  appState?: 'foreground' | 'background'
  activeFeatureFlags?: string[]
}

// The public capture-logger interface lives in @posthog/types as `Logger`. Core
// also exports a `Logger` (the SDK's internal warn/info/error logger). Alias the
// public one to avoid the name collision inside this package.
import type { Logger as CaptureLoggerType } from '@posthog/types'
export type CaptureLogger = CaptureLoggerType

import type { LogAttributeValue, CaptureLogOptions, OtlpLogRecord } from '@posthog/types'

export interface BufferedLogEntry {
  record: OtlpLogRecord
}

/**
 * Pre-send filter. Inspect, mutate, or drop a captured record before it
 * enters the rate-cap or the queue. Return the (possibly transformed) record
 * to keep it; return `null` to drop it.
 *
 * Configure as a single fn or an array. Arrays form a left-to-right chain:
 * each fn receives the previous fn's return value. A `null` from any link
 * short-circuits the chain and drops the record.
 *
 * Runs *before* the rate cap so dropped records don't consume the
 * per-interval budget. Throwing fns are logged and skipped — the chain
 * continues with the previous return value, so a buggy filter degrades to a
 * no-op rather than crashing `captureLog()`.
 *
 * @example Redact secrets from log bodies
 * ```ts
 * logs: {
 *   beforeSend: (record) => ({
 *     ...record,
 *     body: record.body.replace(/api_key=\S+/g, 'api_key=[REDACTED]'),
 *   }),
 * }
 * ```
 *
 * @example Drop noisy debug logs in production
 * ```ts
 * logs: {
 *   beforeSend: (record) => (record.level === 'debug' ? null : record),
 * }
 * ```
 */
export type BeforeSendLogFn = (record: CaptureLogOptions) => CaptureLogOptions | null

/**
 * Configuration for the logs feature on `new PostHog(key, { logs: ... })`.
 * All fields are optional; per-SDK defaults apply (mobile vs browser tune
 * differently for cellular cost vs tab-suspension behavior).
 */
export interface PostHogLogsConfig {
  /**
   * Service name attached to every record as the OTLP `service.name`
   * resource attribute. Used by the Logs UI for filtering / grouping.
   * Default: `'unknown_service'`.
   */
  serviceName?: string

  /**
   * Service version attached as OTLP `service.version`. Useful for
   * correlating regressions to specific app releases.
   */
  serviceVersion?: string

  /**
   * Deployment environment attached as OTLP `deployment.environment`
   * (e.g. `'production'`, `'staging'`, `'dev'`).
   */
  environment?: string

  /**
   * Extra OTLP resource attributes attached to every record. Spread first;
   * SDK-controlled keys (`service.name`, `telemetry.sdk.*`, RN's `os.*`)
   * are layered on top so users cannot accidentally clobber them. Use the
   * dedicated `serviceName` / `environment` / `serviceVersion` fields to
   * override those keys.
   */
  resourceAttributes?: Record<string, LogAttributeValue>

  /**
   * How often the periodic background flush fires (ms). Records also flush
   * eagerly when the buffer fills, on AppState changes (RN), and on
   * `shutdown()`. Lower values trade battery/bandwidth for fresher data.
   * Default: 10000 (RN) / 3000 (browser).
   */
  flushIntervalMs?: number

  /**
   * Max records held in memory before the queue evicts the oldest on push
   * (FIFO). Bounds memory footprint and on-disk-queue size. When the buffer
   * hits this size, an immediate flush is triggered to reclaim space; if
   * the flush hasn't completed before the next capture, the oldest record
   * is shifted out. Default: 100.
   */
  maxBufferSize?: number

  /**
   * Max records per outbound POST. Keeps each request under the server's
   * 2 MB cap. On a 413 response, the SDK halves this value, retries the
   * same records, then ramps back up by 1 per healthy send. A 413 on a
   * single-record batch drops the record (it's larger than the server can
   * accept regardless of batch size). Default: 50 (RN) / 100 (browser).
   */
  maxBatchRecordsPerPost?: number

  /**
   * Tumbling-window rate cap. Bounds how many records can be captured
   * within a sliding (technically tumbling) time window. Records exceeding
   * the cap are dropped synchronously at `captureLog()` (they never enter
   * the buffer or consume bandwidth). A single warn line is logged per
   * window when the cap is hit.
   *
   * Defaults are per-SDK; on RN the default is `{ maxLogs: 500, windowMs:
   * 10000 }` (≈50 logs/sec ceiling, tuned for cellular bandwidth).
   *
   * @example Allow brief bursts up to 1000/min
   * ```ts
   * logs: { rateCap: { maxLogs: 1000, windowMs: 60000 } }
   * ```
   *
   * @example Disable the cap entirely (unbounded)
   * ```ts
   * logs: { rateCap: { maxLogs: undefined } }
   * ```
   */
  rateCap?: {
    /**
     * Max records accepted per `windowMs` window. `undefined` = unbounded.
     */
    maxLogs?: number
    /**
     * Window length in ms. Tumbling, not sliding — the counter resets the
     * first time a capture fires after the window expires.
     */
    windowMs?: number
  }

  /**
   * Pre-send filter. See {@link BeforeSendLogFn} for shape and examples.
   * Configure as a single function or a chain.
   */
  beforeSend?: BeforeSendLogFn | BeforeSendLogFn[]
}

// Fields PostHogLogs needs resolved at runtime. The host SDK fills in its
// defaults and hands the resolved config to the PostHogLogs constructor.
// Flat names internally — public API uses `rateCap: { maxLogs, windowMs }`.
export interface ResolvedPostHogLogsConfig extends Omit<PostHogLogsConfig, 'rateCap'> {
  maxBufferSize: number
  flushIntervalMs: number
  maxBatchRecordsPerPost: number
  rateCapWindowMs: number
  maxLogsPerInterval?: number
  backgroundFlushBudgetMs: number
  terminationFlushBudgetMs: number
}
