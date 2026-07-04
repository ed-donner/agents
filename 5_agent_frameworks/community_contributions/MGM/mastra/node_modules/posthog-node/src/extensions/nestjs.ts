import type { IncomingHttpHeaders } from 'node:http'
import { Observable, throwError } from 'rxjs'
import { catchError } from 'rxjs/operators'

import ErrorTracking from './error-tracking'
import { addProperty, getFirstHeaderValue, getPostHogTracingHeaderValues } from './tracing-headers'
import { PostHogBackendClient } from '../client'

// Local interfaces to avoid runtime dependency on @nestjs/common
interface HttpArgumentsHost {
  getRequest<T = any>(): T
  getResponse<T = any>(): T
}

interface ExecutionContext {
  switchToHttp(): HttpArgumentsHost
}

interface CallHandler<T = any> {
  handle(): Observable<T>
}

interface NestInterceptor<T = any, R = any> {
  intercept(context: ExecutionContext, next: CallHandler<T>): Observable<R>
}

export interface ExceptionCaptureOptions {
  /** Minimum HTTP status code to capture. Exceptions with a lower status (e.g. 4xx) are skipped. @default 500 */
  minStatusToCapture?: number
}

export interface PostHogInterceptorOptions {
  /** Enable exception capture. Pass `true` for defaults or an object to configure. @default false */
  captureExceptions?: boolean | ExceptionCaptureOptions
}

function getClientIp(headers: IncomingHttpHeaders, request: any): string | undefined {
  const forwarded = getFirstHeaderValue(headers['x-forwarded-for'])
  if (forwarded) {
    const ip = forwarded.split(',')[0].trim()
    if (ip) return ip
  }
  return request?.socket?.remoteAddress
}

function getExceptionStatus(exception: unknown): number | undefined {
  if (
    exception &&
    typeof exception === 'object' &&
    'getStatus' in exception &&
    typeof (exception as any).getStatus === 'function'
  ) {
    const status = (exception as any).getStatus()
    return typeof status === 'number' ? status : undefined
  }
  return undefined
}

export class PostHogInterceptor implements NestInterceptor {
  private posthog: PostHogBackendClient
  private captureExceptions: boolean
  private minStatusToCapture: number

  constructor(posthog: PostHogBackendClient, options?: PostHogInterceptorOptions) {
    this.posthog = posthog
    const capture = options?.captureExceptions
    this.captureExceptions = !!capture
    this.minStatusToCapture = (typeof capture === 'object' ? capture.minStatusToCapture : undefined) ?? 500
  }

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const httpHost = context.switchToHttp()
    const request = httpHost.getRequest()
    const response = httpHost.getResponse()

    const headers = (request?.headers ?? {}) as IncomingHttpHeaders
    const { sessionId, distinctId } = getPostHogTracingHeaderValues(headers)

    const properties: Record<string, any> = {}
    addProperty(properties, '$current_url', request?.url)
    addProperty(properties, '$request_method', request?.method)
    addProperty(properties, '$request_path', request?.path ?? request?.url)
    addProperty(properties, '$user_agent', getFirstHeaderValue(headers['user-agent']))
    addProperty(properties, '$ip', getClientIp(headers, request))

    const contextData = {
      ...(sessionId !== undefined ? { sessionId } : {}),
      ...(distinctId !== undefined ? { distinctId } : {}),
      properties,
    }

    // Use enterContext so the context propagates through RxJS Observable
    // subscription and catchError handlers, not just the synchronous callback.
    this.posthog.enterContext(contextData)

    let source = next.handle()

    if (this.captureExceptions) {
      source = source.pipe(
        catchError((exception: unknown) => {
          if (ErrorTracking.isPreviouslyCapturedError(exception)) {
            return throwError(() => exception)
          }
          const status = getExceptionStatus(exception)
          if (status !== undefined && status < this.minStatusToCapture) {
            return throwError(() => exception)
          }
          const responseStatus = status ?? response?.statusCode
          const additionalProperties: Record<string, any> | undefined =
            responseStatus !== undefined ? { $response_status_code: responseStatus } : undefined
          this.posthog.captureException(exception, distinctId, additionalProperties)
          return throwError(() => exception)
        })
      )
    }
    return source
  }
}
