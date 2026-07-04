'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const ThreadStream = require('..')
const { version } = require('../package.json')

test('get context', (t, done) => {
  const stream = new ThreadStream({
    filename: join(__dirname, 'get-context.js'),
    workerData: {},
    sync: true
  })
  t.after(() => stream.end())
  stream.on('context', (ctx) => {
    assert.deepStrictEqual(ctx.threadStreamVersion, version)
    done()
  })
  stream.write('hello')
})
