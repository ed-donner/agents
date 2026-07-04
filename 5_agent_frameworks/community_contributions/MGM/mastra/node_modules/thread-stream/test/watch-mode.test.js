'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { once } = require('events')
const { join } = require('path')
const ThreadStream = require('..')

test('ignores worker messages without a protocol code', async function () {
  const stream = new ThreadStream({
    filename: join(__dirname, 'message-without-code.js'),
    sync: false
  })

  const errors = []
  stream.on('error', err => {
    errors.push(err)
  })

  const ready = once(stream, 'ready')
  const close = once(stream, 'close')

  assert.ok(stream.write('hello world\n'))
  stream.end()

  await ready
  await close

  assert.deepStrictEqual(errors, [])
})
