import { test } from 'node:test'
import assert from 'node:assert'
import { readFile } from 'fs'
import ThreadStream from '../index.js'
import { join } from 'desm'
import { pathToFileURL } from 'url'
import { file } from './helper.js'

function basic (text, filename) {
  test(text, function (t, done) {
    const dest = file()
    const stream = new ThreadStream({
      filename,
      workerData: { dest },
      sync: true
    })

    stream.on('finish', () => {
      readFile(dest, 'utf8', (err, data) => {
        assert.ifError(err)
        assert.strictEqual(data, 'hello world\nsomething else\n')
      })
    })

    stream.on('close', () => {
      done()
    })

    assert.ok(stream.write('hello world\n'))
    assert.ok(stream.write('something else\n'))

    stream.end()
  })
}

basic('esm with path', join(import.meta.url, 'to-file.mjs'))
basic('esm with file URL', pathToFileURL(join(import.meta.url, 'to-file.mjs')).href)

basic('(ts -> es6) esm with path', join(import.meta.url, 'ts', 'to-file.es6.mjs'))
basic('(ts -> es6) esm with file URL', pathToFileURL(join(import.meta.url, 'ts', 'to-file.es6.mjs')).href)

basic('(ts -> es2017) esm with path', join(import.meta.url, 'ts', 'to-file.es2017.mjs'))
basic('(ts -> es2017) esm with file URL', pathToFileURL(join(import.meta.url, 'ts', 'to-file.es2017.mjs')).href)

basic('(ts -> esnext) esm with path', join(import.meta.url, 'ts', 'to-file.esnext.mjs'))
basic('(ts -> esnext) esm with file URL', pathToFileURL(join(import.meta.url, 'ts', 'to-file.esnext.mjs')).href)
