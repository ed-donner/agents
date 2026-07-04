'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { file } = require('./helper')
const { stat } = require('fs')
const ThreadStream = require('..')

test('string limit', { skip: process.env.CI, timeout: 30000 }, (t, done) => {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  let length = 0

  stream.on('close', () => {
    stat(dest, (err, f) => {
      assert.ifError(err)
      assert.strictEqual(f.size, length)
      done()
    })
  })

  const buf = Buffer.alloc(1024).fill('x').toString() // 1 KB

  // This writes 1 GB of data
  for (let i = 0; i < 1024 * 1024; i++) {
    length += buf.length
    stream.write(buf)
  }

  stream.end()
})
