import { PostHogPersistedProperty } from '../types'
import type { Logger } from '../types'
import { PostHogLogs } from './index'
import type { BufferedLogEntry, ResolvedPostHogLogsConfig } from './types'

// Default resolved config for tests — mirrors what each SDK would build by
// merging user config onto its own defaults. Test-only fixture; the real
// defaults live per-SDK. Takes the resolved (flat) shape directly so tests
// can override `maxLogsPerInterval` / `rateCapWindowMs` without going through
// the public `rateCap: { maxLogs, windowMs }` wrapper.
const DEFAULT_MAX_BUFFER_SIZE = 100
const DEFAULT_FLUSH_INTERVAL_MS = 10000
const DEFAULT_MAX_BATCH_RECORDS_PER_POST = 50
const DEFAULT_RATE_CAP_WINDOW_MS = 10000
const DEFAULT_BACKGROUND_FLUSH_BUDGET_MS = 25000
const DEFAULT_TERMINATION_FLUSH_BUDGET_MS = 2000
const resolveForTest = (partial?: Partial<ResolvedPostHogLogsConfig>): ResolvedPostHogLogsConfig => ({
  ...partial,
  maxBufferSize: partial?.maxBufferSize ?? DEFAULT_MAX_BUFFER_SIZE,
  flushIntervalMs: partial?.flushIntervalMs ?? DEFAULT_FLUSH_INTERVAL_MS,
  maxBatchRecordsPerPost: partial?.maxBatchRecordsPerPost ?? DEFAULT_MAX_BATCH_RECORDS_PER_POST,
  rateCapWindowMs: partial?.rateCapWindowMs ?? DEFAULT_RATE_CAP_WINDOW_MS,
  backgroundFlushBudgetMs: DEFAULT_BACKGROUND_FLUSH_BUDGET_MS,
  terminationFlushBudgetMs: DEFAULT_TERMINATION_FLUSH_BUDGET_MS,
  // Uncapped by default so existing tests aren't affected. The rate-limit
  // describe block opts in explicitly via { maxLogsPerInterval: N }.
  maxLogsPerInterval: partial?.maxLogsPerInterval,
})

// Mock PostHog instance exposing the `PostHogCoreStateless` surface PostHogLogs
// touches. Init gating is injected separately via the onReady closure.
const createMockInstance = (overrides: Record<string, any> = {}): any => {
  const store: Record<string, any> = {}
  const instance: any = {
    optedOut: false,
    getDistinctId: jest.fn(() => 'user-123'),
    getSessionId: jest.fn(() => 'sess-456'),
    getLibraryId: jest.fn(() => 'posthog-core-tests'),
    getLibraryVersion: jest.fn(() => '0.0.0-test'),
    getPersistedProperty: jest.fn((key: string) => store[key]),
    setPersistedProperty: jest.fn((key: string, value: any) => {
      if (value === null || value === undefined) {
        delete store[key]
      } else {
        store[key] = value
      }
    }),
    _sendLogsBatch: jest.fn(() => Promise.resolve({ kind: 'ok' })),
    addPendingPromise: jest.fn(<T>(promise: Promise<T>) => promise),
    _store: store,
    ...overrides,
  }
  return instance
}

// Default onReady for tests — runs fn synchronously, matching a post-init SDK.
// Tests that model pre-init or rejected init provide their own closure.
const immediateOnReady = (fn: () => void): void => fn()

const createMockLogger = (): Logger => {
  const logger: any = {
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    critical: jest.fn(),
  }
  logger.createLogger = jest.fn(() => logger)
  return logger as Logger
}

const readQueue = (instance: any): BufferedLogEntry[] => {
  return (instance._store[PostHogPersistedProperty.LogsQueue] as BufferedLogEntry[] | undefined) ?? []
}

// Default getContext closure for tests — reads from the mock instance the way
// a real SDK adapter would. Tests that need dynamic context override per-call.
const getContextFor = (instance: any) => (): { distinctId?: string; sessionId?: string } => ({
  distinctId: instance.getDistinctId() || undefined,
  sessionId: instance.getSessionId() || undefined,
})

describe('PostHogLogs', () => {
  let mockInstance: any
  let logger: Logger

  beforeEach(() => {
    mockInstance = createMockInstance()
    logger = createMockLogger()
  })

  it('constructs without throwing', () => {
    const logs = new PostHogLogs(mockInstance, resolveForTest(), logger, getContextFor(mockInstance), immediateOnReady)
    expect(logs).toBeDefined()
  })

  describe('captureLog', () => {
    it('writes a record to the logs queue via setPersistedProperty', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'hello world' })

      const queue = readQueue(mockInstance)
      expect(queue).toHaveLength(1)
      expect(queue[0].record.body).toEqual({ stringValue: 'hello world' })
      expect(mockInstance.setPersistedProperty).toHaveBeenCalledWith(
        PostHogPersistedProperty.LogsQueue,
        expect.any(Array)
      )
    })

    it('maps severity levels correctly', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'oh no', level: 'error' })

      const queue = readQueue(mockInstance)
      expect(queue[0].record.severityText).toBe('ERROR')
      expect(queue[0].record.severityNumber).toBe(17)
    })

    it('defaults to INFO when no level is provided', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'hello' })

      const queue = readQueue(mockInstance)
      expect(queue[0].record.severityText).toBe('INFO')
    })

    it('auto-populates distinctId and sessionId', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'test' })

      const queue = readQueue(mockInstance)
      const attrs = Object.fromEntries(queue[0].record.attributes.map((a: any) => [a.key, a.value]))
      expect(attrs['posthogDistinctId']).toEqual({ stringValue: 'user-123' })
      expect(attrs['sessionId']).toEqual({ stringValue: 'sess-456' })
    })

    it('merges user attributes over auto-populated ones', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'test', attributes: { posthogDistinctId: 'override' } })

      const queue = readQueue(mockInstance)
      const attrs = Object.fromEntries(queue[0].record.attributes.map((a: any) => [a.key, a.value]))
      expect(attrs['posthogDistinctId']).toEqual({ stringValue: 'override' })
    })

    it('is a no-op when body is empty', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: '' })
      expect(readQueue(mockInstance)).toHaveLength(0)
      expect(mockInstance.setPersistedProperty).not.toHaveBeenCalled()
    })

    it('is a no-op when body is missing', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({} as any)
      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('is a no-op when optedOut is true', () => {
      const instance = createMockInstance({ optedOut: true })
      const logs = new PostHogLogs(instance, resolveForTest(), logger, getContextFor(instance), immediateOnReady)
      logs.captureLog({ body: 'should be dropped' })
      expect(readQueue(instance)).toHaveLength(0)
    })

    it('captures unconditionally — only optedOut, missing body, and beforeSend can drop', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'kept' })
      expect(readQueue(mockInstance)).toHaveLength(1)
    })

    it('appends subsequent captures to the existing queue', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'first' })
      logs.captureLog({ body: 'second' })
      logs.captureLog({ body: 'third' })

      const queue = readQueue(mockInstance)
      expect(queue).toHaveLength(3)
      expect(queue[0].record.body.stringValue).toBe('first')
      expect(queue[1].record.body.stringValue).toBe('second')
      expect(queue[2].record.body.stringValue).toBe('third')
    })

    it('drops the oldest record when buffer overflows maxBufferSize', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBufferSize: 3 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )

      logs.captureLog({ body: 'one' })
      logs.captureLog({ body: 'two' })
      logs.captureLog({ body: 'three' })
      logs.captureLog({ body: 'four' })

      const queue = readQueue(mockInstance)
      expect(queue).toHaveLength(3)
      expect(queue.map((e) => e.record.body.stringValue)).toEqual(['two', 'three', 'four'])
    })

    it('logs a diagnostic when evicting on overflow', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBufferSize: 1 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )

      logs.captureLog({ body: 'first' })
      logs.captureLog({ body: 'second' })

      expect(logger.info).toHaveBeenCalledWith('Logs queue is full, dropping oldest record.')
    })

    it('passes trace context through to the OTLP record', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({
        body: 'trace test',
        trace_id: '4bf92f3577b34da6a3ce929d0e0e4736',
        span_id: '00f067aa0ba902b7',
        trace_flags: 1,
      })

      const queue = readQueue(mockInstance)
      expect(queue[0].record.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736')
      expect(queue[0].record.spanId).toBe('00f067aa0ba902b7')
      expect(queue[0].record.flags).toBe(1)
    })
  })

  // captureLog routes deferred work through the injected onReady closure. These
  // tests exercise that contract by substituting a custom onReady.
  describe('init gating via onReady', () => {
    it('defers captures until onReady runs fn, then drains in order', () => {
      const pending: Array<() => void> = []
      const defer = (fn: () => void): void => {
        pending.push(fn)
      }

      mockInstance._store[PostHogPersistedProperty.LogsQueue] = [
        { record: { body: { stringValue: 'prior-session' } } as any },
      ]

      const logs = new PostHogLogs(mockInstance, resolveForTest(), logger, getContextFor(mockInstance), defer)
      logs.captureLog({ body: 'before-init' })

      expect(mockInstance.setPersistedProperty).not.toHaveBeenCalled()

      pending.forEach((fn) => fn())

      const queue = readQueue(mockInstance)
      expect(queue).toHaveLength(2)
      expect(queue[0].record.body.stringValue).toBe('prior-session')
      expect(queue[1].record.body.stringValue).toBe('before-init')
    })

    it('silently drops captures when onReady never invokes fn (rejected init)', () => {
      const neverReady = jest.fn(() => {
        /* simulate rejected init: fn is never called */
      })
      const logs = new PostHogLogs(mockInstance, resolveForTest(), logger, getContextFor(mockInstance), neverReady)

      logs.captureLog({ body: 'dropped' })

      expect(readQueue(mockInstance)).toHaveLength(0)
      expect(mockInstance.setPersistedProperty).not.toHaveBeenCalled()
      expect(neverReady).toHaveBeenCalledTimes(1)
    })

    it('builds record with capture-time context even when onReady defers drain', () => {
      const pending: Array<() => void> = []
      const defer = (fn: () => void): void => {
        pending.push(fn)
      }
      const instance = createMockInstance({
        getDistinctId: jest.fn().mockReturnValue('user-A'),
      })

      const logs = new PostHogLogs(instance, resolveForTest(), logger, getContextFor(instance), defer)
      logs.captureLog({ body: 'captured-as-user-A' })

      instance.getDistinctId = jest.fn().mockReturnValue('user-B')

      pending.forEach((fn) => fn())

      const queue = readQueue(instance)
      expect(queue).toHaveLength(1)
      const attrs = Object.fromEntries(queue[0].record.attributes.map((a: any) => [a.key, a.value]))
      expect(attrs['posthogDistinctId']).toEqual({ stringValue: 'user-A' })
    })

    it('captureLog does not throw to the caller', () => {
      const neverReady = (): void => {
        /* simulate rejected init */
      }
      const logs = new PostHogLogs(mockInstance, resolveForTest(), logger, getContextFor(mockInstance), neverReady)

      expect(() => logs.captureLog({ body: 'after-reject-1' })).not.toThrow()
      expect(() => logs.captureLog({ body: 'after-reject-2' })).not.toThrow()
    })
  })

  describe('flush', () => {
    it('is a no-op when the queue is empty', async () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      await logs.flush()
      expect(mockInstance._sendLogsBatch).not.toHaveBeenCalled()
    })

    it('drains the queue and sends an OTLP payload with resource + scope attrs', async () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ serviceName: 'my-service', environment: 'prod', serviceVersion: '1.2.3' }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'one' })
      logs.captureLog({ body: 'two' })

      await logs.flush()

      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
      const payload = mockInstance._sendLogsBatch.mock.calls[0][0]
      const resourceAttrs = Object.fromEntries(
        payload.resourceLogs[0].resource.attributes.map((a: any) => [a.key, a.value])
      )
      expect(resourceAttrs['service.name']).toEqual({ stringValue: 'my-service' })
      expect(resourceAttrs['deployment.environment']).toEqual({ stringValue: 'prod' })
      expect(resourceAttrs['service.version']).toEqual({ stringValue: '1.2.3' })
      // OTLP-standard SDK identification — pulled from the instance's
      // getLibraryId/Version so every SDK self-identifies.
      expect(resourceAttrs['telemetry.sdk.name']).toEqual({ stringValue: 'posthog-core-tests' })
      expect(resourceAttrs['telemetry.sdk.version']).toEqual({ stringValue: '0.0.0-test' })

      const scope = payload.resourceLogs[0].scopeLogs[0].scope
      expect(scope).toEqual({ name: 'posthog-core-tests', version: '0.0.0-test' })

      const bodies = payload.resourceLogs[0].scopeLogs[0].logRecords.map((r: any) => r.body.stringValue)
      expect(bodies).toEqual(['one', 'two'])

      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('defaults service.name to "unknown_service" when not configured', async () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'hi' })
      await logs.flush()

      const attrs = Object.fromEntries(
        mockInstance._sendLogsBatch.mock.calls[0][0].resourceLogs[0].resource.attributes.map((a: any) => [
          a.key,
          a.value,
        ])
      )
      expect(attrs['service.name']).toEqual({ stringValue: 'unknown_service' })
    })

    it('SDK-controlled telemetry.sdk.* and service.name win over user resourceAttributes', async () => {
      // Most logs backends index on these keys for routing, SDK-version
      // dashboards, and bug-correlation. Letting a stray user key clobber
      // them silently breaks ingestion attribution, so the layout puts
      // user attrs first and SDK identity attrs on top.
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({
          resourceAttributes: {
            'telemetry.sdk.name': 'my-wrapper',
            'service.name': 'user-supplied-service',
            // Non-protected user keys still pass through.
            'host.name': 'my-host',
          },
        }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'hi' })
      await logs.flush()

      const attrs = Object.fromEntries(
        mockInstance._sendLogsBatch.mock.calls[0][0].resourceLogs[0].resource.attributes.map((a: any) => [
          a.key,
          a.value,
        ])
      )
      expect(attrs['telemetry.sdk.name']).toEqual({ stringValue: 'posthog-core-tests' })
      expect(attrs['telemetry.sdk.version']).toEqual({ stringValue: '0.0.0-test' })
      expect(attrs['service.name']).toEqual({ stringValue: 'unknown_service' })
      expect(attrs['host.name']).toEqual({ stringValue: 'my-host' })
    })

    it('splits a large queue into multiple batches of maxBatchRecordsPerPost and persists after each', async () => {
      const sendOrder: number[] = []
      let persistCallsBeforeSecondSend = 0
      mockInstance._sendLogsBatch = jest.fn(async (payload: any) => {
        // Record the persist count *at the start of* send #2. The first send
        // must have already persisted its queue advance by then — otherwise a
        // crash between sends could double-send the first batch.
        if (sendOrder.length === 1) {
          persistCallsBeforeSecondSend = mockInstance.setPersistedProperty.mock.calls.length
        }
        sendOrder.push(payload.resourceLogs[0].scopeLogs[0].logRecords.length)
        return { kind: 'ok' }
      })
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 2, maxBufferSize: 10 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      for (let i = 0; i < 5; i++) {
        logs.captureLog({ body: `msg-${i}` })
      }

      await logs.flush()

      // 2 + 2 + 1 = 5 records across 3 POSTs
      expect(sendOrder).toEqual([2, 2, 1])
      // After the first send, the queue must have been persisted before the second send —
      // otherwise a crash between sends could double-send the first batch.
      expect(persistCallsBeforeSecondSend).toBeGreaterThan(5 /* enqueue writes */)
      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('halves maxBatchRecordsPerPost and retries the same records on too-large outcome', async () => {
      const sendSizes: number[] = []
      mockInstance._sendLogsBatch = jest.fn(async (payload: any) => {
        const size = payload.resourceLogs[0].scopeLogs[0].logRecords.length
        sendSizes.push(size)
        if (sendSizes.length === 1) {
          return { kind: 'too-large' }
        }
        return { kind: 'ok' }
      })
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 4, maxBufferSize: 10 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      for (let i = 0; i < 4; i++) {
        logs.captureLog({ body: `msg-${i}` })
      }

      await logs.flush()

      // First POST: 4 records → too-large. Retry with halved cap = 2, so: 2 + 2.
      expect(sendSizes).toEqual([4, 2, 2])
      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('ramps maxBatchRecordsPerPost back toward the configured cap after a healthy streak', async () => {
      // Reproduces the Greptile P1 concern: a one-off oversized payload
      // should not permanently degrade throughput. After a 413 halves the
      // cap, each healthy send grows it back by 1 until the configured
      // maximum is reached.
      const sendSizes: number[] = []
      mockInstance._sendLogsBatch = jest.fn(async (payload: any) => {
        const size = payload.resourceLogs[0].scopeLogs[0].logRecords.length
        sendSizes.push(size)
        // First POST is rejected as too-large; everything else succeeds.
        if (sendSizes.length === 1) {
          return { kind: 'too-large' }
        }
        return { kind: 'ok' }
      })
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 4, maxBufferSize: 100 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      // Enqueue plenty so the recovery has room to ramp.
      for (let i = 0; i < 16; i++) {
        logs.captureLog({ body: `msg-${i}` })
      }

      await logs.flush()

      // First POST: 4 records → too-large. Cap halves to 2. From there each
      // healthy send grows the cap by 1 toward the configured 4:
      //   sizes: [4 (413), 2, 3, 4, 4, ...] (the trailing 3 drains the
      //   remainder of the 16-record queue).
      expect(sendSizes).toEqual([4, 2, 3, 4, 4, 3])
      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('drops the only record when too-large arrives on a batch of size 1', async () => {
      mockInstance._sendLogsBatch = jest.fn(() => Promise.resolve({ kind: 'too-large' }))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 1 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'too-big' })

      await logs.flush()

      // Batch of 1 that's rejected as too-large is permanent — drop it rather
      // than spin on the same record forever.
      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('warns explicitly when dropping a size-1 413 (visibility for the lost record)', async () => {
      mockInstance._sendLogsBatch = jest.fn(() => Promise.resolve({ kind: 'too-large' }))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 1 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'oversized' })
      await logs.flush()

      expect(logger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Dropping a single log record after 413 with batch size 1')
      )
    })

    it('keeps draining the queue after a size-1 413 drop (one bad record does not stall the pipeline)', async () => {
      // First record returns too-large with size 1 (drops and warns), then
      // the rest of the queue should continue flushing normally.
      let callCount = 0
      mockInstance._sendLogsBatch = jest.fn(() => {
        callCount++
        return Promise.resolve(callCount === 1 ? { kind: 'too-large' } : { kind: 'ok' })
      })
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 1, maxBufferSize: 10 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'oversized' })
      logs.captureLog({ body: 'ok-1' })
      logs.captureLog({ body: 'ok-2' })

      await logs.flush()

      // Three sends: oversized (dropped), ok-1, ok-2. Queue is empty.
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(3)
      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('size-1 413 retry-shrink path: starts at maxBatchRecordsPerPost, halves to 1, drops at 1', async () => {
      // Realistic flow: batch=N gets too-large, halves to N/2, halves to 1,
      // then 413 on size 1 is the permanent drop. Verifies the cap actually
      // shrinks all the way down before the size-1 drop fires.
      const sendSizes: number[] = []
      mockInstance._sendLogsBatch = jest.fn(async (payload: any) => {
        const size = payload.resourceLogs[0].scopeLogs[0].logRecords.length
        sendSizes.push(size)
        return { kind: 'too-large' }
      })
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 4, maxBufferSize: 10 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      // Single oversized record. With maxBatchRecordsPerPost=4 but only 1 record
      // in the queue, the first send is size 1 — going straight to the drop path.
      logs.captureLog({ body: 'huge' })

      await logs.flush()

      // Single send of size 1, dropped immediately (no halving rounds because
      // batch was already at 1).
      expect(sendSizes).toEqual([1])
      expect(readQueue(mockInstance)).toHaveLength(0)
      expect(logger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Dropping a single log record after 413 with batch size 1')
      )
    })

    it('keeps records in the queue on retry-later outcome and re-throws the carried error', async () => {
      const netErr = new Error('offline')
      mockInstance._sendLogsBatch = jest.fn(() => Promise.resolve({ kind: 'retry-later', error: netErr }))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'queued' })

      await expect(logs.flush()).rejects.toBe(netErr)

      expect(readQueue(mockInstance)).toHaveLength(1)
    })

    it('drops the batch on fatal outcome and re-throws the carried error', async () => {
      const bogus = new Error('malformed')
      mockInstance._sendLogsBatch = jest.fn(() => Promise.resolve({ kind: 'fatal', error: bogus }))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'doomed' })

      await expect(logs.flush()).rejects.toBe(bogus)

      expect(readQueue(mockInstance)).toHaveLength(0)
    })

    it('awaits _waitForStoragePersist between batches so a crash can’t replay records', async () => {
      const sequence: string[] = []
      mockInstance._sendLogsBatch = jest.fn(async (payload: any) => {
        sequence.push(`send:${payload.resourceLogs[0].scopeLogs[0].logRecords.length}`)
        return { kind: 'ok' }
      })
      const waitForStoragePersist = jest.fn(async () => {
        sequence.push('waitForPersist')
      })
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 2, maxBufferSize: 10 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady,
        waitForStoragePersist
      )
      for (let i = 0; i < 3; i++) {
        logs.captureLog({ body: `msg-${i}` })
      }

      await logs.flush()

      // Send 2 → waitForPersist → send 1 → waitForPersist. If the wait
      // landed out-of-order (e.g. before send), a crash mid-batch could
      // replay records on the next startup.
      expect(sequence).toEqual(['send:2', 'waitForPersist', 'send:1', 'waitForPersist'])
      expect(waitForStoragePersist).toHaveBeenCalledTimes(2)
    })

    it('serializes concurrent flush calls rather than racing them', async () => {
      let resolveFirst: (v: any) => void = () => {}
      mockInstance._sendLogsBatch = jest.fn(
        () =>
          new Promise((r) => {
            resolveFirst = r
          })
      )
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'a' })

      const first = logs.flush()
      const second = logs.flush()

      // Both callers observe the same in-flight promise, so only one POST happens.
      resolveFirst({ kind: 'ok' })
      await Promise.all([first, second])
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })
  })

  describe('flush triggers', () => {
    beforeEach(() => jest.useFakeTimers())
    afterEach(() => jest.useRealTimers())

    it('fires a flush when the buffer hits maxBufferSize', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBufferSize: 3 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'a' })
      logs.captureLog({ body: 'b' })
      expect(mockInstance._sendLogsBatch).not.toHaveBeenCalled()

      logs.captureLog({ body: 'c' })
      // Threshold trigger fires `flush()` fire-and-forget; the call happens
      // synchronously on the hot path.
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })

    it('schedules one timer per idle window and fires flush on expiry', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ flushIntervalMs: 5000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'first' })
      logs.captureLog({ body: 'second' })
      logs.captureLog({ body: 'third' })

      // Only one timer armed, not three — subsequent enqueues inside the
      // window must not push the flush out.
      expect(mockInstance._sendLogsBatch).not.toHaveBeenCalled()
      jest.advanceTimersByTime(4999)
      expect(mockInstance._sendLogsBatch).not.toHaveBeenCalled()
      jest.advanceTimersByTime(1)
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })

    it('does not schedule a timer for the threshold-triggered path', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBufferSize: 2, flushIntervalMs: 5000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'a' })
      logs.captureLog({ body: 'b' })
      // Threshold path flushed already; advancing time must not trigger a second send.
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
      jest.advanceTimersByTime(5000)
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })
  })

  describe('shutdown', () => {
    beforeEach(() => jest.useFakeTimers())
    afterEach(() => jest.useRealTimers())

    it('drains the queue and clears any armed flush timer', async () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ flushIntervalMs: 5000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'a' })
      // A timer is now armed — shutdown must cancel it so the process can
      // exit cleanly even if the final flush triggers a duplicate send.

      await logs.shutdown()

      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
      // Advancing past the original interval must not produce a second flush.
      jest.advanceTimersByTime(10000)
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })

    it('swallows flush errors so shutdown can complete', async () => {
      mockInstance._sendLogsBatch = jest.fn(() => Promise.resolve({ kind: 'fatal', error: new Error('boom') }))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'doomed' })

      await expect(logs.shutdown()).resolves.toBeUndefined()
    })

    it('is a no-op when the queue is empty and no timer is armed', async () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      await logs.shutdown()
      expect(mockInstance._sendLogsBatch).not.toHaveBeenCalled()
    })

    it('called twice is idempotent (second call is a no-op once queue drains)', async () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'x' })
      await logs.shutdown()
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)

      // Queue is empty now — a second shutdown shouldn't re-send.
      await logs.shutdown()
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })

    it('while a flush is in flight, the shared promise coordinates a single drain', async () => {
      let resolveFirst: (v: any) => void = () => {}
      mockInstance._sendLogsBatch = jest.fn(
        () =>
          new Promise((r) => {
            resolveFirst = r
          })
      )
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'a' })

      // Real timers only here — shutdown(timeoutMs) path uses safeSetTimeout,
      // which is incompatible with the default `jest.useFakeTimers()`.
      jest.useRealTimers()

      const flushP = logs.flush()
      const shutdownP = logs.shutdown()

      resolveFirst({ kind: 'ok' })
      await Promise.all([flushP, shutdownP])

      // Both callers joined the same in-flight flush — no double-send.
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)
    })

    it('races the final flush against timeoutMs so a stalled send does not hang shutdown', async () => {
      jest.useRealTimers()
      // _sendLogsBatch never resolves — the budget must force shutdown to return.
      mockInstance._sendLogsBatch = jest.fn(() => new Promise(() => {}))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'stuck' })

      const start = Date.now()
      await logs.shutdown(30)
      const elapsed = Date.now() - start

      // Loose upper bound — just prove we didn't wait forever.
      expect(elapsed).toBeLessThan(500)
    })

    it('propagates a _waitForStoragePersist rejection out of flush (so callers can react)', async () => {
      const persistErr = new Error('disk is gone')
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest(),
        logger,
        getContextFor(mockInstance),
        immediateOnReady,
        // Persist fails AFTER the HTTP send succeeds — records were sent but
        // the queue-advance didn't reach disk. Surface the error so the
        // caller knows a retry on restart may re-send.
        () => Promise.reject(persistErr)
      )
      logs.captureLog({ body: 'sent-but-not-persisted' })

      await expect(logs.flush()).rejects.toBe(persistErr)
    })
  })

  describe('beforeSend hook', () => {
    // Helper that hides the constructor boilerplate so the table-driven
    // cases below can be a single line of setup each.
    const makeLogs = (beforeSend: PostHogLogsConfig['beforeSend']): PostHogLogs =>
      new PostHogLogs(
        mockInstance,
        resolveForTest({ beforeSend }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )

    // Cases that share a "captureLog → assert queue body" shape. Bespoke
    // assertions (logger expectations, throw-drops-the-record) live in their
    // own `it` blocks below — those were warping the table when forced into it.
    type Case = {
      name: string
      beforeSend: PostHogLogsConfig['beforeSend']
      input: string
      expectedQueueLen: number
      expectedBody?: string
    }
    const cases: Case[] = [
      {
        name: 'transforms body when fn returns mutated value',
        beforeSend: (r) => ({ ...r, body: r.body.toUpperCase() }),
        input: 'hello',
        expectedQueueLen: 1,
        expectedBody: 'HELLO',
      },
      {
        name: 'drops the record when fn returns null',
        beforeSend: () => null,
        input: 'silent',
        expectedQueueLen: 0,
      },
      {
        name: 'chains an array left-to-right (each fn sees previous result)',
        beforeSend: [
          (r) => ({ ...r, body: `${r.body}-1` }),
          (r) => ({ ...r, body: `${r.body}-2` }),
          (r) => ({ ...r, body: `${r.body}-3` }),
        ],
        input: 'x',
        expectedQueueLen: 1,
        expectedBody: 'x-1-2-3',
      },
      {
        name: 'short-circuits the chain when any fn returns null',
        beforeSend: [(r) => r, () => null, (r) => r],
        input: 'dropped',
        expectedQueueLen: 0,
      },
      {
        name: 'treats an empty body returned by beforeSend as a drop',
        beforeSend: (r) => ({ ...r, body: '' }),
        input: 'will-be-emptied',
        expectedQueueLen: 0,
      },
    ]

    it.each(cases)('$name', ({ beforeSend, input, expectedQueueLen, expectedBody }) => {
      const logs = makeLogs(beforeSend)
      logs.captureLog({ body: input })

      const queue = readQueue(mockInstance)
      expect(queue).toHaveLength(expectedQueueLen)
      if (expectedBody !== undefined) {
        expect(queue[0].record.body.stringValue).toBe(expectedBody)
      }
    })

    it('logs an info line when a fn returns null', () => {
      // Carved out because the table only asserts queue shape; this
      // verifies the diagnostic path that warns the user a record was
      // dropped by their filter (no other knob to surface that).
      const logs = makeLogs(() => null)
      logs.captureLog({ body: 'silent' })
      expect(logger.info).toHaveBeenCalledWith('Log was rejected in beforeSend function')
    })

    it('never crashes the caller when a fn throws — drops the record (fail closed) and logs', () => {
      const thrower = jest.fn(() => {
        throw new Error('bad filter')
      })
      const after = jest.fn((r: any) => ({ ...r, body: `${r.body}!` }))
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ beforeSend: [thrower, after] }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )

      expect(() => logs.captureLog({ body: 'hi' })).not.toThrow()
      expect(readQueue(mockInstance)).toHaveLength(0)
      expect(after).not.toHaveBeenCalled()
      expect(logger.error).toHaveBeenCalledWith(
        expect.stringContaining('Error in beforeSend function for log:'),
        expect.any(Error)
      )
    })
  })

  describe('rate limiting', () => {
    beforeEach(() => jest.useFakeTimers({ now: 0 }))
    afterEach(() => jest.useRealTimers())

    // Tabular form for the simple in-window cap cases. Bespoke ones
    // (warn-once, window-roll reset, clock-jump backward, beforeSend
    // accounting) keep their own `it` blocks because they assert
    // multi-window or interleaving behavior.
    type CapCase = {
      name: string
      maxLogsPerInterval: number | undefined
      capturesInWindow: number
      expectedQueueLen: number
    }
    const capCases: CapCase[] = [
      {
        name: 'is uncapped when maxLogsPerInterval is undefined (default)',
        maxLogsPerInterval: undefined,
        capturesInWindow: 50,
        expectedQueueLen: 50,
      },
      {
        name: 'drops captures beyond maxLogsPerInterval within the window',
        maxLogsPerInterval: 3,
        capturesInWindow: 5,
        expectedQueueLen: 3,
      },
    ]

    it.each(capCases)('$name', ({ maxLogsPerInterval, capturesInWindow, expectedQueueLen }) => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxLogsPerInterval, rateCapWindowMs: 1000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      for (let i = 0; i < capturesInWindow; i++) {
        logs.captureLog({ body: `msg-${i}` })
      }
      expect(readQueue(mockInstance)).toHaveLength(expectedQueueLen)
    })

    it('warns exactly once per window when dropping, regardless of how many drops', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxLogsPerInterval: 2, rateCapWindowMs: 1000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      for (let i = 0; i < 10; i++) {
        logs.captureLog({ body: `msg-${i}` })
      }
      expect(logger.warn).toHaveBeenCalledTimes(1)
      expect(logger.warn).toHaveBeenCalledWith(expect.stringContaining('captureLog dropping logs'))
    })

    it('resets the counter when the window rolls (and warns again on next overflow)', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxLogsPerInterval: 1, rateCapWindowMs: 1000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'window-1-kept' })
      logs.captureLog({ body: 'window-1-dropped' })
      expect(readQueue(mockInstance)).toHaveLength(1)
      expect(logger.warn).toHaveBeenCalledTimes(1)

      jest.setSystemTime(1001)
      logs.captureLog({ body: 'window-2-kept' })
      logs.captureLog({ body: 'window-2-dropped' })
      expect(readQueue(mockInstance)).toHaveLength(2)
      expect(logger.warn).toHaveBeenCalledTimes(2)
    })

    it('resets the window when the clock jumps backward (NTP correction / manual clock change)', () => {
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxLogsPerInterval: 2, rateCapWindowMs: 1000 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      // Seed the window at t=5000, fill the budget.
      jest.setSystemTime(5000)
      logs.captureLog({ body: 'a' })
      logs.captureLog({ body: 'b' })
      logs.captureLog({ body: 'dropped-pre-jump' })
      expect(readQueue(mockInstance)).toHaveLength(2)

      // Clock jumps backward by 1 hour (e.g. user reset device time).
      // Without the `elapsed < 0` guard, the rate cap would stay "stuck"
      // until `now` exceeds the old window-start again — potentially
      // dropping every log for the duration of the backward jump.
      jest.setSystemTime(5000 - 60 * 60 * 1000)
      logs.captureLog({ body: 'accepted-post-jump' })

      expect(readQueue(mockInstance)).toHaveLength(3)
      expect(readQueue(mockInstance)[2].record.body.stringValue).toBe('accepted-post-jump')
    })

    it('beforeSend-rejected records do not consume the per-interval budget', () => {
      // beforeSend drops the first record; rate cap is 1 per window. The
      // SECOND capture should still succeed — if beforeSend consumed the
      // budget, it'd be dropped.
      const beforeSend = jest
        .fn()
        .mockReturnValueOnce(null)
        .mockImplementation((r: any) => r)
      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxLogsPerInterval: 1, rateCapWindowMs: 1000, beforeSend }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'pre-filtered-out' })
      logs.captureLog({ body: 'should-still-fit' })

      expect(readQueue(mockInstance)).toHaveLength(1)
      expect(readQueue(mockInstance)[0].record.body.stringValue).toBe('should-still-fit')
    })
  })

  describe('concurrent capture during flush', () => {
    it('mid-flush captures land in the queue for the next cycle — not lost, not double-sent', async () => {
      let resolveSend: (v: any) => void = () => {}
      let captureDuringSend: (() => void) | null = null

      mockInstance._sendLogsBatch = jest.fn(
        () =>
          new Promise((r) => {
            if (captureDuringSend) {
              captureDuringSend()
              captureDuringSend = null
            }
            resolveSend = (v) => r(v)
          })
      )

      const logs = new PostHogLogs(
        mockInstance,
        resolveForTest({ maxBatchRecordsPerPost: 1, maxBufferSize: 10 }),
        logger,
        getContextFor(mockInstance),
        immediateOnReady
      )
      logs.captureLog({ body: 'first' })
      captureDuringSend = (): void => {
        logs.captureLog({ body: 'mid-flight' })
      }

      const flushP = logs.flush()
      await new Promise((r) => setImmediate(r))
      resolveSend({ kind: 'ok' })
      await flushP

      // flush() uses `originalQueueLength` at entry, so a mid-flight capture
      // is intentionally left for the NEXT flush (matches events semantics).
      // The invariant we care about: not lost, not double-sent.
      expect(readQueue(mockInstance)).toHaveLength(1)
      expect(readQueue(mockInstance)[0].record.body.stringValue).toBe('mid-flight')
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(1)

      // A subsequent flush picks it up — no data lost.
      const flushP2 = logs.flush()
      await new Promise((r) => setImmediate(r))
      resolveSend({ kind: 'ok' })
      await flushP2
      expect(readQueue(mockInstance)).toHaveLength(0)
      expect(mockInstance._sendLogsBatch).toHaveBeenCalledTimes(2)
    })
  })
})
