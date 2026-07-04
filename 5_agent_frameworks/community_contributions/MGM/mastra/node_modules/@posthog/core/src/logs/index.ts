import type { LogAttributeValue } from '@posthog/types'
import { buildOtlpLogRecord, buildOtlpLogsPayload } from './logs-utils'
import { Logger, PostHogPersistedProperty } from '../types'
import type { PostHogCoreStateless } from '../posthog-core-stateless'
import { isArray, safeSetTimeout } from '../utils'
import type {
  BeforeSendLogFn,
  BufferedLogEntry,
  CaptureLogOptions,
  LogSdkContext,
  ResolvedPostHogLogsConfig,
} from './types'

export class PostHogLogs {
  private _maxBufferSize: number
  private _flushIntervalMs: number
  // Mutable — halved on 413 to shrink the next POST, and ramped back up by
  // one record after each successful send so a one-off oversized payload
  // (e.g. a giant stack trace) doesn't permanently degrade throughput.
  private _maxBatchRecordsPerPost: number
  private _flushTimer?: ReturnType<typeof safeSetTimeout>
  // Serializes concurrent flushes — the second caller awaits the first rather
  // than racing it and double-sending the same head-of-queue records.
  private _flushPromise: Promise<void> | null = null

  // Fixed-window rate cap. Tumbling (not sliding) for cheap arithmetic on the
  // hot path. Window rolls the first time `captureLog` fires after the window
  // expires — no background timer needed. `_droppedWarned` keeps the log noise
  // to one line per window regardless of how many records got dropped.
  private _rateCapWindowMs: number
  private _maxLogsPerInterval?: number
  private _intervalWindowStart = 0
  private _intervalLogCount = 0
  private _droppedWarned = false

  constructor(
    private readonly _instance: PostHogCoreStateless,
    private readonly _config: ResolvedPostHogLogsConfig,
    private readonly _logger: Logger,
    private readonly _getContext: () => LogSdkContext,
    private readonly _onReady: (fn: () => void) => void,
    // Waits for the logs-storage persist to hit disk. Called between batches
    // so a crash after a successful HTTP send but before the queue-advance
    // reaches disk can't cause duplicate records on next startup. SDKs with
    // synchronous storage (or no async persist layer) can pass a no-op. RN
    // wires this to its dedicated `_logsStorage.waitForPersist()`.
    private readonly _waitForStoragePersist: () => Promise<void> = () => Promise.resolve()
  ) {
    this._maxBufferSize = _config.maxBufferSize
    this._flushIntervalMs = _config.flushIntervalMs
    this._maxBatchRecordsPerPost = _config.maxBatchRecordsPerPost
    this._rateCapWindowMs = _config.rateCapWindowMs
    this._maxLogsPerInterval = _config.maxLogsPerInterval
  }

  captureLog(options: CaptureLogOptions): void {
    if (this._instance.isDisabled) {
      return
    }
    if (this._instance.optedOut) {
      return
    }
    if (!options?.body) {
      return
    }

    // Ordering: beforeSend → rate cap → OTLP build. beforeSend runs first so
    // user-dropped records don't consume the per-interval budget.
    const filtered = this._runBeforeSend(options)
    if (filtered === null) {
      return
    }
    // beforeSend could return a record with empty body — treat as drop.
    if (!filtered.body) {
      return
    }

    if (!this._checkRateLimit()) {
      return
    }

    // Build before deferring so attributes reflect state at capture time, not
    // at drain time (identity/session changes between capture and drain must
    // not corrupt recorded attributes).
    const record = buildOtlpLogRecord(filtered, this._getContext())
    const entry: BufferedLogEntry = { record }

    this._onReady(() => this._enqueue(entry))
  }

  /**
   * Runs the configured `beforeSend` hook(s) on a capture record:
   *   - single fn OR array of fns (chain, left-to-right)
   *   - returning `null` drops the record (logged at info)
   *   - a thrown error is logged and the record is dropped
   */
  private _runBeforeSend(options: CaptureLogOptions): CaptureLogOptions | null {
    const beforeSend = this._config.beforeSend
    if (!beforeSend) {
      return options
    }
    const fns = isArray(beforeSend) ? beforeSend : [beforeSend]
    let result: CaptureLogOptions = options
    for (const fn of fns) {
      try {
        const next = fn(result)
        if (!next) {
          this._logger.info(`Log was rejected in beforeSend function`)
          return null
        }
        result = next
      } catch (e) {
        this._logger.error(`Error in beforeSend function for log:`, e)
        return null
      }
    }
    return result
  }

  /**
   * Returns `true` if this capture fits within the current rate-cap window,
   * `false` if it should be dropped.
   *
   * Fixed (tumbling) window: the counter resets the first time `captureLog`
   * fires after `rateCapWindowMs` has elapsed — no timer needed.
   * `maxLogsPerInterval === undefined` means unbounded.
   *
   * Wall-clock safety: if `Date.now()` jumps backward (manual device-clock
   * change, big NTP correction), `elapsed` goes negative. We treat that the
   * same as "window expired" and reset — otherwise the rate cap would be
   * stuck until the clock caught up to the old window start, potentially
   * dropping logs for hours.
   *
   * Pre-init note: the counter increments here, before `_onReady` defers
   * `_enqueue` to the init promise. If init resolves slowly and the user is
   * later opted out, the counter has already consumed budget for records
   * that won't enqueue. Cosmetic — no record is "lost" beyond what's
   * already gated, and the window rolls on its own.
   */
  private _checkRateLimit(): boolean {
    if (this._maxLogsPerInterval === undefined) {
      return true
    }
    const now = Date.now()
    const elapsed = now - this._intervalWindowStart
    if (elapsed >= this._rateCapWindowMs || elapsed < 0) {
      this._intervalWindowStart = now
      this._intervalLogCount = 0
      this._droppedWarned = false
    }
    if (this._intervalLogCount >= this._maxLogsPerInterval) {
      if (!this._droppedWarned) {
        this._logger.warn(
          `captureLog dropping logs: exceeded ${this._maxLogsPerInterval} logs per ${this._rateCapWindowMs}ms`
        )
        this._droppedWarned = true
      }
      return false
    }
    this._intervalLogCount++
    return true
  }

  /**
   * Drains `LogsQueue` in `maxBatchRecordsPerPost` slices, POSTing each as an
   * OTLP payload.
   *   - Network error   → keep items in queue, re-throw (caller retries later)
   *   - 413             → halve batch size, retry same records (do not advance)
   *   - Any other error → drop the batch (avoid infinite loop on malformed data),
   *                       re-throw so callers can log/report
   * Concurrent calls are serialized through `_flushPromise` so records at the
   * head of the queue can't be sent twice.
   */
  async flush(): Promise<void> {
    if (this._instance.isDisabled) {
      return
    }
    if (this._flushPromise) {
      return this._flushPromise
    }
    this._flushPromise = this._flushInner().finally(() => {
      this._flushPromise = null
    })
    return this._flushPromise
  }

  private async _flushInner(): Promise<void> {
    this._clearFlushTimer()

    let queue = this._instance.getPersistedProperty<BufferedLogEntry[]>(PostHogPersistedProperty.LogsQueue) ?? []
    if (queue.length === 0) {
      return
    }

    const originalQueueLength = queue.length
    let sentCount = 0

    while (queue.length > 0 && sentCount < originalQueueLength) {
      const batchSize = Math.min(queue.length, this._maxBatchRecordsPerPost)
      const batch = queue.slice(0, batchSize)
      const records = batch.map((e) => e.record)

      const payload = buildOtlpLogsPayload(
        records,
        this._buildResourceAttributes(),
        this._instance.getLibraryId(),
        this._instance.getLibraryVersion()
      )

      const outcome = await this._instance._sendLogsBatch(payload)

      if (outcome.kind === 'too-large' && batch.length > 1) {
        this._maxBatchRecordsPerPost = Math.max(1, Math.floor(batch.length / 2))
        this._logger.warn(
          `Received 413 when sending logs batch of size ${batch.length}, reducing batch size to ${this._maxBatchRecordsPerPost}`
        )
        // Don't advance the queue — retry the same records with the smaller cap.
        continue
      }

      if (outcome.kind === 'retry-later') {
        // Network error: keep records in the queue for the next flush cycle
        // and surface the error so the caller can log/react.
        throw outcome.error
      }

      // ok | fatal | too-large-with-batch-of-1 → records are leaving the
      // queue. 'fatal' and size-1 413s are dropped so we don't spin on the
      // same record forever. Surface the size-1 413 explicitly so a single
      // oversized record (e.g. a giant body field) is visible in logs
      // instead of silently disappearing.
      if (outcome.kind === 'too-large') {
        this._logger.warn(
          'Dropping a single log record after 413 with batch size 1 — the record is larger than the server cap and cannot be split further.'
        )
      } else if (outcome.kind === 'ok' && this._maxBatchRecordsPerPost < this._config.maxBatchRecordsPerPost) {
        // Linear recovery: each healthy send pushes the cap back up by 1
        // toward the configured maximum. Linear (not doubling) so we don't
        // immediately retrigger a 413 if the previous shrink was justified.
        this._maxBatchRecordsPerPost = Math.min(this._config.maxBatchRecordsPerPost, this._maxBatchRecordsPerPost + 1)
      }
      await this._persistQueueAdvance(batch.length)
      queue = this._instance.getPersistedProperty<BufferedLogEntry[]>(PostHogPersistedProperty.LogsQueue) ?? []
      sentCount += batch.length

      if (outcome.kind === 'fatal') {
        throw outcome.error
      }
    }
  }

  private async _persistQueueAdvance(consumed: number): Promise<void> {
    // Re-read the queue in case captures landed mid-flush, then drop the head.
    const refreshed = this._instance.getPersistedProperty<BufferedLogEntry[]>(PostHogPersistedProperty.LogsQueue) ?? []
    this._instance.setPersistedProperty(PostHogPersistedProperty.LogsQueue, refreshed.slice(consumed))
    // Wait for the advance to hit disk before the next batch sends, matching
    // events' `flushStorage()` contract. Prevents duplicates if the app crashes
    // after the HTTP success but before the queue-advance persists.
    await this._waitForStoragePersist()
  }

  /**
   * OTLP resource attributes for every batch.
   *
   * Layout: user `resourceAttributes` spread first, then SDK-controlled
   * keys layered on top so users cannot accidentally clobber them. Most logs
   * backends index on `service.name` and `telemetry.sdk.*` for routing,
   * SDK-version dashboards, and bug-correlation; letting a stray user key
   * overwrite them silently breaks ingestion attribution. The dedicated
   * `serviceName` / `environment` / `serviceVersion` config fields are the
   * supported way to override `service.name` / `deployment.environment` /
   * `service.version`.
   */
  private _buildResourceAttributes(): Record<string, LogAttributeValue> {
    return {
      ...this._config.resourceAttributes,
      'service.name': this._config.serviceName || 'unknown_service',
      ...(this._config.environment && { 'deployment.environment': this._config.environment }),
      ...(this._config.serviceVersion && { 'service.version': this._config.serviceVersion }),
      'telemetry.sdk.name': this._instance.getLibraryId(),
      'telemetry.sdk.version': this._instance.getLibraryVersion(),
    }
  }

  private _enqueue(entry: BufferedLogEntry): void {
    // Re-check optedOut: preload may have hydrated the real persisted value,
    // or optIn/optOut may have fired while this fn was deferred.
    if (this._instance.optedOut) {
      return
    }

    const queue = this._instance.getPersistedProperty<BufferedLogEntry[]>(PostHogPersistedProperty.LogsQueue) ?? []
    if (queue.length >= this._maxBufferSize) {
      queue.shift()
      this._logger.info('Logs queue is full, dropping oldest record.')
    }
    queue.push(entry)
    this._instance.setPersistedProperty(PostHogPersistedProperty.LogsQueue, queue)

    // Threshold trigger: at-capacity means flushing now reclaims space before
    // the next capture has to shift something out.
    if (queue.length >= this._maxBufferSize) {
      this._flushInBackground()
      return
    }

    // Timer trigger: only arm one timer at a time. A subsequent enqueue within
    // the window shouldn't reschedule — that would keep pushing the flush out.
    if (!this._flushTimer) {
      this._flushTimer = safeSetTimeout(() => {
        this._flushTimer = undefined
        this._flushInBackground()
      }, this._flushIntervalMs)
    }
  }

  /**
   * Stops the timer-based flush and sends anything still in the queue.
   * Intended for process-teardown paths (RN `_shutdown` override). Swallows
   * errors so a failing final flush can't block the broader shutdown.
   *
   * If `timeoutMs` is provided, the final flush races against that budget so
   * a slow network/storage can't hold up shutdown indefinitely. Without it,
   * flush time is bounded only by `fetchRetryCount * (requestTimeout +
   * fetchRetryDelay)`, which can exceed the caller's shutdown SLA.
   */
  async shutdown(timeoutMs?: number): Promise<void> {
    this._clearFlushTimer()
    const flushPromise = this.flush().catch(() => {
      // Best-effort: a logs-flush failure during shutdown is not actionable
      // and must not prevent the rest of shutdown from running. Errors are
      // still surfaced from the regular `flush()` path in normal operation.
    })
    if (timeoutMs === undefined) {
      await flushPromise
      return
    }
    await Promise.race([flushPromise, new Promise<void>((resolve) => safeSetTimeout(resolve, timeoutMs))])
  }

  /**
   * Time-bounded flush for transient lifecycle events (e.g. RN
   * foreground→background) that must complete inside an OS-imposed window.
   * Unlike `shutdown`, this leaves the periodic flush timer in place so the
   * pipeline keeps draining if the process is resumed instead of suspended.
   *
   * Errors propagate so the host SDK can route them through its standard
   * lifecycle error handler (e.g. RN's `logFlushError`). If the timer wins
   * the race, a late rejection from the in-flight flush is silenced via a
   * no-op handler attached after the race settles, to avoid noisy
   * unhandled-rejection logs — the next regular flush cycle will retry.
   */
  async flushWithTimeout(timeoutMs: number): Promise<void> {
    let timedOut = false
    const flushPromise = this.flush()
    const timerPromise = new Promise<void>((resolve) =>
      safeSetTimeout(() => {
        timedOut = true
        resolve()
      }, timeoutMs)
    )
    try {
      await Promise.race([flushPromise, timerPromise])
    } finally {
      if (timedOut) {
        // Race lost — flush is still in flight. Attach a no-op rejection
        // handler so a late failure isn't logged as unhandled.
        void flushPromise.catch(() => {})
      }
    }
  }

  private _flushInBackground(): void {
    void this.flush().catch((err) => {
      this._logger.error('PostHog logs flush failed:', err)
    })
  }

  private _clearFlushTimer(): void {
    if (this._flushTimer) {
      clearTimeout(this._flushTimer)
      this._flushTimer = undefined
    }
  }
}
