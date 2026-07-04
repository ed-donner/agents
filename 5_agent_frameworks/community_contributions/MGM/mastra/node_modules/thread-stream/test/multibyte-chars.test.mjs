import { test } from 'node:test'
import assert from 'node:assert'
import { readFile } from 'fs'
import ThreadStream from '../index.js'
import { join } from 'desm'
import { file } from './helper.js'

test('break up utf8 multibyte (sync)', (t, done) => {
  const longString = '\u03A3'.repeat(16)

  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 15, // this must be odd
    filename: join(import.meta.url, 'to-file.js'),
    workerData: { dest },
    sync: true
  })

  stream.on('finish', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, longString)
      done()
    })
  })

  stream.write(longString)
  stream.end()
})

test('break up utf8 multibyte (async)', (t, done) => {
  const longString = '\u03A3'.repeat(16)

  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 15, // this must be odd
    filename: join(import.meta.url, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  stream.on('finish', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, longString)
      done()
    })
  })

  stream.write(longString)
  stream.end()
})

test('break up utf8 multibyte several times bigger than write buffer', (t, done) => {
  const longString = '\u03A3'.repeat(32)

  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 15, // this must be odd
    filename: join(import.meta.url, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  stream.on('finish', () => {
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, longString)
      done()
    })
  })

  stream.write(longString)
  stream.end()
})
