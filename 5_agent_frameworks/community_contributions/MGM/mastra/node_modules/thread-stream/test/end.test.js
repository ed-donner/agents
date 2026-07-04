'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { readFile } = require('fs')
const { file } = require('./helper')
const ThreadStream = require('..')

test('destroy support', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file-on-destroy.js'),
    workerData: { dest },
    sync: true
  })

  stream.on('close', () => {
    assert.ok(!stream.writable)
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, 'hello world\nsomething else\n')
      done()
    })
  })

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))
  assert.ok(stream.writable)

  stream.end()
})

test('synchronous _final support', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file-on-final.js'),
    workerData: { dest },
    sync: true
  })

  stream.on('close', () => {
    assert.ok(!stream.writable)
    readFile(dest, 'utf8', (err, data) => {
      assert.ifError(err)
      assert.strictEqual(data, 'hello world\nsomething else\n')
      done()
    })
  })

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))
  assert.ok(stream.writable)

  stream.end()
})
