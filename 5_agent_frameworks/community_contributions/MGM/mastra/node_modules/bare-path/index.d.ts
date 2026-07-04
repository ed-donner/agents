declare namespace path {
  export const sep: '/' | '\\'
  export const delimiter: ':' | ';'

  export function basename(path: string, suffix?: string): string

  export function dirname(path: string): string

  export function extname(path: string): string

  export function isAbsolute(path: string): boolean

  export function join(...paths: string[]): string

  export function normalize(path: string): string

  export function relative(from: string, to: string): string

  export function resolve(...args: string[]): string

  export function toNamespacedPath(path: string): string

  export const posix = path
  export const win32 = path
}

export = path
