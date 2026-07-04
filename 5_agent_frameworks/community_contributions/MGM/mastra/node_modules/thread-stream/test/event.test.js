'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const ThreadStream = require('..')

test('event propagate', (t, done) => {
  const stream = new ThreadStream({
    filename: join(__dirname, 'emit-event.js'),
    workerData: {},
    sync: true
  })
  t.after(() => stream.end())
  stream.on('socketError', function (a, b, c, n, error) {
    assert.deepStrictEqual(a, 'list')
    assert.deepStrictEqual(b, 'of')
    assert.deepStrictEqual(c, 'args')
    assert.deepStrictEqual(n, 123)
    assert.deepStrictEqual(error, new Error('unable to write data to the TCP socket'))
    done()
  })
  stream.write('hello')
})
