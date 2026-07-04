export interface ContextData {
  distinctId?: string
  sessionId?: string
  properties?: Record<string, any>
}

export interface ContextOptions {
  /**
   * If true, replaces the current context entirely.
   * If false, merges with the existing context (new values override existing ones).
   * @default false
   */
  fresh?: boolean
}

export interface IPostHogContext {
  get(): ContextData | undefined
  run<T>(context: ContextData, fn: () => T, options?: ContextOptions): T
  enter(context: ContextData, options?: ContextOptions): void
}
