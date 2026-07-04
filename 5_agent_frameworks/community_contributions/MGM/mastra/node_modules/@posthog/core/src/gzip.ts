import { Compression } from './types'

/**
 * Older browsers and some runtimes don't support this yet
 * This API (as of 2025-05-07) is not available on React Native.
 */
export function isGzipSupported(): boolean {
  return (
    'CompressionStream' in globalThis &&
    'TextEncoder' in globalThis &&
    'Response' in globalThis &&
    typeof Response.prototype.blob === 'function'
  )
}

const NATIVE_GZIP_VALIDATION_ERROR = 'NativeGzipValidationError'
const GZIP_MAGIC_FIRST_BYTE = 0x1f
const GZIP_MAGIC_SECOND_BYTE = 0x8b
const GZIP_DEFLATE_METHOD = 0x08

const hasGzipMagic = (bytes: Uint8Array): boolean => {
  return bytes.length >= 2 && bytes[0] === GZIP_MAGIC_FIRST_BYTE && bytes[1] === GZIP_MAGIC_SECOND_BYTE
}

export const isGzipData = (body: unknown): boolean => {
  if (body instanceof ArrayBuffer) {
    return hasGzipMagic(new Uint8Array(body))
  }

  if (ArrayBuffer.isView(body)) {
    return hasGzipMagic(new Uint8Array(body.buffer, body.byteOffset, body.byteLength))
  }

  return false
}

export const isGzipRequest = (compression?: unknown, urlCompression?: unknown): boolean => {
  return compression === Compression.GZipJS || urlCompression === Compression.GZipJS || urlCompression === 'gzip'
}

export const isNativeAsyncGzipReadError = (error: unknown): boolean => {
  if (!error || typeof error !== 'object') {
    return false
  }

  const name = 'name' in error ? String(error.name) : ''

  return name === 'NotReadableError'
}

export const isNativeAsyncGzipError = (error: unknown): boolean => {
  if (!error || typeof error !== 'object') {
    return false
  }

  const name = 'name' in error ? String(error.name) : ''

  return isNativeAsyncGzipReadError(error) || name === NATIVE_GZIP_VALIDATION_ERROR
}

type NativeGzipValidationReason = 'too-short' | 'invalid-header' | 'invalid-crc' | 'invalid-size'

let crc32Table: number[] | undefined

const getCrc32Table = (): number[] => {
  if (crc32Table) {
    return crc32Table
  }

  crc32Table = []
  for (let i = 0; i < 256; i++) {
    let crc = i
    for (let j = 0; j < 8; j++) {
      crc = crc & 1 ? 0xedb88320 ^ (crc >>> 1) : crc >>> 1
    }
    crc32Table[i] = crc >>> 0
  }
  return crc32Table
}

const crc32 = (bytes: Uint8Array): number => {
  const table = getCrc32Table()
  let crc = 0xffffffff
  for (let i = 0; i < bytes.length; i++) {
    crc = table[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8)
  }
  return (crc ^ 0xffffffff) >>> 0
}

const throwNativeGzipValidationError = (reason: NativeGzipValidationReason): never => {
  const error = new Error(`Native gzip produced invalid output: ${reason}`)
  error.name = NATIVE_GZIP_VALIDATION_ERROR
  throw error
}

const validateNativeGzip = async (compressed: Blob, inputBytes: Uint8Array): Promise<void> => {
  if (compressed.size < 18) {
    throwNativeGzipValidationError('too-short')
  }

  const header = new Uint8Array(await compressed.slice(0, 10).arrayBuffer())
  if (!hasGzipMagic(header) || header[2] !== GZIP_DEFLATE_METHOD) {
    throwNativeGzipValidationError('invalid-header')
  }

  const trailer = new DataView(await compressed.slice(compressed.size - 8).arrayBuffer())
  if (trailer.getUint32(0, true) !== crc32(inputBytes)) {
    throwNativeGzipValidationError('invalid-crc')
  }

  const inputSize = inputBytes.length >>> 0
  if (trailer.getUint32(4, true) !== inputSize) {
    throwNativeGzipValidationError('invalid-size')
  }
}

export type GzipCompressOptions = {
  /**
   * By default this helper swallows compression errors and returns null.
   * Some browsers, notably Safari 16, can throw NotReadableError from the
   * native CompressionStream path. Callers can opt into rethrowing so they
   * can detect that case and change future compression behavior if needed.
   */
  rethrow?: boolean
}

/**
 * Gzip a string using Compression Streams API if it's available
 */
export async function gzipCompress(input: string, isDebug = true, options?: GzipCompressOptions): Promise<Blob | null> {
  try {
    const inputBytes = new TextEncoder().encode(input)
    const compressedStream = new CompressionStream('gzip')
    const writer = compressedStream.writable.getWriter()

    const writePromise = writer
      .write(inputBytes)
      .then(() => writer.close())
      .catch(async (err) => {
        try {
          await writer.abort(err)
        } catch {
          // Ignore abort failures and rethrow the original compression error below.
        }
        throw err
      })
    const responsePromise = new Response(compressedStream.readable).blob()

    const [compressed] = await Promise.all([responsePromise, writePromise])
    await validateNativeGzip(compressed, inputBytes)
    return compressed
  } catch (error) {
    if (options?.rethrow) {
      throw error
    }

    if (isDebug) {
      console.error('Failed to gzip compress data', error)
    }
    return null
  }
}
