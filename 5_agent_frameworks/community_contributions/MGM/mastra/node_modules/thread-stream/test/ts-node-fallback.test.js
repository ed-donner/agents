'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { readFile } = require('fs/promises')
const { join } = require('path')
const { file } = require('./helper')
const ThreadStream = require('..')

// This test verifies that TypeScript files can be loaded via ts-node
// when native type stripping is not enabled in the worker thread.
// Unlike ts.test.ts which passes --experimental-strip-types via execArgv,
// this test does NOT pass that flag, so the worker will fall back to ts-node.
test('typescript module with ts-node fallback', async function (t) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'ts', 'to-file.ts'),
    workerData: { dest },
    sync: false
  })

  t.after(() => stream.end())

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))

  stream.end()

  await new Promise((resolve) => {
    stream.on('close', resolve)
  })

  const data = await readFile(dest, 'utf8')
  assert.strictEqual(data, 'hello world\nsomething else\n')
})
