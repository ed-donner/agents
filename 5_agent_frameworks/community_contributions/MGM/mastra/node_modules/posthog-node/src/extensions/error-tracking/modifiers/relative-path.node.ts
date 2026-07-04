import { ErrorTracking as CoreErrorTracking } from '@posthog/core'
import { relative, isAbsolute, sep } from 'path'

export function createRelativePathModifier(basePath: string = process.cwd()) {
  const isWindows = sep === '\\'
  const toUnix = (p: string) => (isWindows ? p.replace(/\\/g, '/') : p)
  const normalizedBase = toUnix(basePath)

  return async (frames: CoreErrorTracking.StackFrame[]): Promise<CoreErrorTracking.StackFrame[]> => {
    for (const frame of frames) {
      if (!frame.filename || frame.filename.startsWith('node:') || frame.filename.startsWith('data:')) {
        continue
      }
      if (isAbsolute(frame.filename)) {
        frame.filename = toUnix(relative(normalizedBase, toUnix(frame.filename)))
      }
    }
    return frames
  }
}
