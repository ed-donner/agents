import { isArray, isNumber, isObject, isString } from '@/utils'

export const EXCEPTION_STEP_INTERNAL_FIELDS = {
  MESSAGE: '$message',
  TIMESTAMP: '$timestamp',
} as const

const RESERVED_EXCEPTION_STEP_KEYS = new Set<string>([
  EXCEPTION_STEP_INTERNAL_FIELDS.MESSAGE,
  EXCEPTION_STEP_INTERNAL_FIELDS.TIMESTAMP,
])

export type ExceptionStep = {
  [EXCEPTION_STEP_INTERNAL_FIELDS.MESSAGE]: string
  [EXCEPTION_STEP_INTERNAL_FIELDS.TIMESTAMP]: string | number
  [key: string]: unknown
}

/** NOTE: This type is also defined in `@posthog/types` (posthog-config.ts). Keep both in sync. */
export type ExceptionStepsConfig = {
  enabled?: boolean
  max_bytes?: number
}

export type ResolvedExceptionStepsConfig = {
  enabled: boolean
  max_bytes: number
}

export const DEFAULT_EXCEPTION_STEPS_CONFIG: ResolvedExceptionStepsConfig = {
  enabled: true,
  max_bytes: 32768, // ~32KB
}

export function resolveExceptionStepsConfig(config?: ExceptionStepsConfig | null): ResolvedExceptionStepsConfig {
  if (!config) {
    return { ...DEFAULT_EXCEPTION_STEPS_CONFIG }
  }

  return {
    enabled: config.enabled ?? DEFAULT_EXCEPTION_STEPS_CONFIG.enabled,
    max_bytes: normalizePositiveInteger(config.max_bytes, DEFAULT_EXCEPTION_STEPS_CONFIG.max_bytes),
  }
}

export function stripReservedExceptionStepFields(properties?: Record<string, unknown> | null): {
  sanitizedProperties: Record<string, unknown>
  droppedKeys: string[]
} {
  if (!properties) {
    return { sanitizedProperties: {}, droppedKeys: [] }
  }

  const droppedKeys: string[] = []
  const sanitizedProperties = Object.keys(properties).reduce<Record<string, unknown>>((acc, key) => {
    if (RESERVED_EXCEPTION_STEP_KEYS.has(key)) {
      droppedKeys.push(key)
      return acc
    }
    acc[key] = properties[key]
    return acc
  }, {})

  return {
    sanitizedProperties,
    droppedKeys,
  }
}

export class ExceptionStepsBuffer {
  private _entries: { step: ExceptionStep; bytes: number }[] = []
  private _totalBytes: number = 0
  private _config: ResolvedExceptionStepsConfig

  constructor(config?: ExceptionStepsConfig | null) {
    this._config = resolveExceptionStepsConfig(config)
  }

  public setConfig(config?: ExceptionStepsConfig | null): void {
    this._config = resolveExceptionStepsConfig(config)
    this._trimToMaxBytes()
  }

  public add(step: ExceptionStep): void {
    const serialized = normalizeAndSerializeStep(step)
    if (!serialized) {
      return
    }

    const bytes = getUtf8ByteLength(serialized.json)
    if (bytes > this._config.max_bytes) {
      return
    }

    this._entries.push({ step: serialized.step, bytes })
    this._totalBytes += bytes
    this._trimToMaxBytes()
  }

  public getAttachable(): ExceptionStep[] {
    return this._entries.map((e) => e.step)
  }

  public clear(): void {
    this._entries = []
    this._totalBytes = 0
  }

  public size(): number {
    return this._entries.length
  }

  private _trimToMaxBytes(): void {
    while (this._totalBytes > this._config.max_bytes && this._entries.length > 0) {
      const evicted = this._entries.shift()
      if (evicted) {
        this._totalBytes -= evicted.bytes
      }
    }
  }
}

function normalizePositiveInteger(input: number | undefined, fallback: number): number {
  if (!isNumber(input) || input === Infinity || input === -Infinity) {
    return fallback
  }

  const normalized = Math.floor(input)
  if (normalized < 0) {
    return fallback
  }

  return normalized
}

function normalizeAndSerializeStep(step: ExceptionStep): { step: ExceptionStep; json: string } | undefined {
  const json = safeStringify(step)
  if (!json) {
    return undefined
  }

  try {
    const parsed = JSON.parse(json)
    if (!isObject(parsed)) {
      return undefined
    }

    const parsedStep = parsed as Record<string, unknown>
    const message = parsedStep[EXCEPTION_STEP_INTERNAL_FIELDS.MESSAGE]
    const timestamp = parsedStep[EXCEPTION_STEP_INTERNAL_FIELDS.TIMESTAMP]

    if (!isString(message) || message.trim().length === 0) {
      return undefined
    }

    if (!isString(timestamp) && !isNumber(timestamp)) {
      return undefined
    }

    return {
      step: parsedStep as ExceptionStep,
      json,
    }
  } catch {
    return undefined
  }
}

function safeStringify(value: unknown): string | undefined {
  const seen = new WeakSet<object>()

  try {
    return JSON.stringify(value, (_key, replacementValue: unknown) => {
      if (typeof replacementValue === 'bigint') {
        return replacementValue.toString()
      }

      if (typeof replacementValue === 'function' || typeof replacementValue === 'symbol') {
        return undefined
      }

      if (replacementValue instanceof Date) {
        return replacementValue.toISOString()
      }

      if (replacementValue instanceof Error) {
        return {
          name: replacementValue.name,
          message: replacementValue.message,
          stack: replacementValue.stack,
        }
      }

      if (replacementValue && typeof replacementValue === 'object') {
        if (seen.has(replacementValue)) {
          return '[Circular]'
        }
        seen.add(replacementValue)
      }

      return replacementValue
    })
  } catch {
    return undefined
  }
}

export function getUtf8ByteLength(value: string): number {
  if (typeof TextEncoder !== 'undefined') {
    return new TextEncoder().encode(value).length
  }

  const encoded = encodeURIComponent(value)
  let byteLength = 0
  for (let i = 0; i < encoded.length; i++) {
    if (encoded[i] === '%') {
      byteLength += 1
      i += 2
    } else {
      byteLength += 1
    }
  }

  return byteLength
}
