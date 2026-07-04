import { AsyncLocalStorage } from 'node:async_hooks'
import { ContextData, ContextOptions, IPostHogContext } from './types'

export class PostHogContext implements IPostHogContext {
  private storage: AsyncLocalStorage<ContextData>

  constructor() {
    this.storage = new AsyncLocalStorage<ContextData>()
  }

  get(): ContextData | undefined {
    return this.storage.getStore()
  }

  run<T>(context: ContextData, fn: () => T, options?: ContextOptions): T {
    return this.storage.run(this.resolve(context, options), fn)
  }

  enter(context: ContextData, options?: ContextOptions): void {
    this.storage.enterWith(this.resolve(context, options))
  }

  private resolve(context: ContextData, options?: ContextOptions): ContextData {
    if (options?.fresh === true) {
      return context
    }

    const current = this.get() || {}
    return {
      distinctId: context.distinctId ?? current.distinctId,
      sessionId: context.sessionId ?? current.sessionId,
      properties: {
        ...(current.properties || {}),
        ...(context.properties || {}),
      },
    }
  }
}
