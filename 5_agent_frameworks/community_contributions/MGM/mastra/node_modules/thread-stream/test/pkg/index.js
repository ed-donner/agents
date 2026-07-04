'use strict'

/**
 * This file is packaged using pkg in order to test if worker.js works in that context.
 * Note: We can't use node:test here because it crashes inside pkg bundles due to V8 internals.
 */

const assert = require('node:assert')
const { join } = require('path')
const { file } = require('../helper')
const ThreadStream = require('../..')

globalThis.__bundlerPathsOverrides = {
  'thread-stream-worker': join(__dirname, '..', 'custom-worker.js')
}

const dest = file()

process.on('uncaughtException', (error) => {
  console.error(error)
  process.exit(1)
})

const stream = new ThreadStream({
  filename: join(__dirname, '..', 'to-file.js'),
  workerData: { dest },
  sync: true
})

stream.worker.removeAllListeners('message')
stream.worker.once('message', (message) => {
  assert.strictEqual(message.code, 'CUSTOM-WORKER-CALLED')
  console.log('pkg test passed')
  process.exit(0)
})

stream.end()
