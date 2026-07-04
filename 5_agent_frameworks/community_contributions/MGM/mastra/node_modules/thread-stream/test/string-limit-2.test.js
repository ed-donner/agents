'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { file } = require('./helper')
const { createReadStream } = require('fs')
const ThreadStream = require('..')
const buffer = require('buffer')

const MAX_STRING = buffer.constants.MAX_STRING_LENGTH

test('string limit 2', { skip: process.env.CI }, (t, done) => {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  stream.on('close', async () => {
    let buf
    for await (const chunk of createReadStream(dest)) {
      buf = chunk
    }
    assert.strictEqual('asd', buf.toString().slice(-3))
    done()
  })

  stream.on('ready', () => {
    stream.write('a'.repeat(MAX_STRING - 2))
    stream.write('asd')
    stream.end()
  })
})
