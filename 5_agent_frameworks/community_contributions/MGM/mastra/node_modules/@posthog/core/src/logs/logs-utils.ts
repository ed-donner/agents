import type {
  CaptureLogOptions,
  LogAttributeValue,
  LogSeverityLevel,
  OtlpAnyValue,
  OtlpKeyValue,
  OtlpLogRecord,
  OtlpLogsPayload,
  OtlpSeverityEntry,
  OtlpSeverityText,
} from '@posthog/types'
import type { LogSdkContext } from './types'
import { isArray, isBoolean, isNull, isUndefined } from '../utils'

// ============================================================================
// Severity mapping
// ============================================================================

const OTLP_SEVERITY_MAP: Record<LogSeverityLevel, OtlpSeverityEntry> = {
  trace: { text: 'TRACE', number: 1 },
  debug: { text: 'DEBUG', number: 5 },
  info: { text: 'INFO', number: 9 },
  warn: { text: 'WARN', number: 13 },
  error: { text: 'ERROR', number: 17 },
  fatal: { text: 'FATAL', number: 21 },
}

const DEFAULT_OTLP_SEVERITY = OTLP_SEVERITY_MAP.info

export function getOtlpSeverityText(level: LogSeverityLevel): OtlpSeverityText {
  return (OTLP_SEVERITY_MAP[level] || DEFAULT_OTLP_SEVERITY).text
}

export function getOtlpSeverityNumber(level: LogSeverityLevel): number {
  return (OTLP_SEVERITY_MAP[level] || DEFAULT_OTLP_SEVERITY).number
}

// ============================================================================
// OTLP AnyValue conversion
// ============================================================================

export function toOtlpAnyValue(value: LogAttributeValue): OtlpAnyValue {
  if (isBoolean(value)) {
    return { boolValue: value }
  }
  // NOTE: typeof check (not core's isNumber) so NaN is included. core's
  // isNumber explicitly excludes NaN via the `x === x` guard, which would
  // route NaN through the JSON.stringify branch below — JSON has no
  // representation for non-finite floats and JSON.stringify turns them into
  // `null`, losing the value server-side. proto3 JSON mapping (which OTLP/HTTP
  // rides) requires the literal strings; we encode them as stringValue to keep
  // the human-readable signal regardless of which downstream parser sees them.
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      return { stringValue: String(value) }
    }
    if (Number.isInteger(value)) {
      return { intValue: value }
    }
    return { doubleValue: value }
  }
  if (typeof value === 'string') {
    return { stringValue: value }
  }
  if (isArray(value)) {
    return { arrayValue: { values: value.map((v) => toOtlpAnyValue(v as LogAttributeValue)) } }
  }
  // Objects fall back to JSON. OTLP supports kvlistValue but the encoder
  // stays flat for simplicity.
  try {
    return { stringValue: JSON.stringify(value) }
  } catch {
    return { stringValue: String(value) }
  }
}

export function toOtlpKeyValueList(attrs: Record<string, LogAttributeValue>): OtlpKeyValue[] {
  const result: OtlpKeyValue[] = []
  for (const key in attrs) {
    const value = attrs[key]
    if (isNull(value) || isUndefined(value)) {
      continue
    }
    result.push({ key, value: toOtlpAnyValue(value) })
  }
  return result
}

// ============================================================================
// OTLP LogRecord construction
// ============================================================================

/**
 * Returns the current wall-clock time as a unix-nanos string.
 *
 * OTLP requires nanoseconds as a string (uint64 doesn't fit in JS Number).
 * `Date.now() * 1_000_000` would exceed Number.MAX_SAFE_INTEGER, so we
 * concatenate instead of multiplying.
 */
function timestampToUnixNano(): string {
  return String(Date.now()) + '000000'
}

/**
 * Builds a single OTLP log record.
 *
 * Auto-attribute population is shape-driven: any field present on `sdkContext`
 * is emitted as the corresponding attribute. Each SDK populates only the
 * fields that apply to it (browser fills `currentUrl`; mobile fills
 * `screenName` / `appState`), so a missing field never adds a stray attribute.
 *
 * User-provided `options.attributes` always wins on conflicts.
 */
export function buildOtlpLogRecord(options: CaptureLogOptions, sdkContext: LogSdkContext): OtlpLogRecord {
  const level: LogSeverityLevel = options.level || 'info'
  const { text: severityText, number: severityNumber } = OTLP_SEVERITY_MAP[level] || DEFAULT_OTLP_SEVERITY
  const now = timestampToUnixNano()

  const autoAttributes: Record<string, LogAttributeValue> = {}

  if (sdkContext.distinctId) {
    autoAttributes.posthogDistinctId = sdkContext.distinctId
  }
  if (sdkContext.sessionId) {
    autoAttributes.sessionId = sdkContext.sessionId
  }
  if (sdkContext.currentUrl) {
    autoAttributes['url.full'] = sdkContext.currentUrl
  }
  if (sdkContext.screenName) {
    autoAttributes['screen.name'] = sdkContext.screenName
  }
  if (sdkContext.appState) {
    autoAttributes['app.state'] = sdkContext.appState
  }
  if (sdkContext.activeFeatureFlags && sdkContext.activeFeatureFlags.length > 0) {
    autoAttributes.feature_flags = sdkContext.activeFeatureFlags
  }

  const mergedAttributes = {
    ...autoAttributes,
    ...(options.attributes || {}),
  }

  const record: OtlpLogRecord = {
    timeUnixNano: now,
    observedTimeUnixNano: now,
    severityNumber,
    severityText,
    body: { stringValue: options.body },
    attributes: toOtlpKeyValueList(mergedAttributes),
  }

  if (options.trace_id) {
    record.traceId = options.trace_id
  }
  if (options.span_id) {
    record.spanId = options.span_id
  }
  if (!isUndefined(options.trace_flags)) {
    record.flags = options.trace_flags
  }

  return record
}

// ============================================================================
// OTLP envelope construction
// ============================================================================

/**
 * Wraps a list of records in the OTLP `resourceLogs` envelope.
 *
 * `scopeName` is the SDK package name (`posthog-js`, `posthog-react-native`,
 * etc.). `scopeVersion` is the SDK semver. The server combines them into a
 * single `instrumentation_scope` field (`{name}@{version}`) used for
 * SDK-version-level attribution in queries and dashboards.
 */
export function buildOtlpLogsPayload(
  logRecords: OtlpLogRecord[],
  resourceAttributes: Record<string, LogAttributeValue>,
  scopeName: string,
  scopeVersion: string
): OtlpLogsPayload {
  return {
    resourceLogs: [
      {
        resource: { attributes: toOtlpKeyValueList(resourceAttributes) },
        scopeLogs: [
          {
            scope: { name: scopeName, version: scopeVersion },
            logRecords,
          },
        ],
      },
    ],
  }
}
