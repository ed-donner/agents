'use strict'

const { test } = require('node:test')
const { join } = require('path')
const ThreadStream = require('..')
const { file } = require('./helper')

const MAX = 1000

let str = ''

for (let i = 0; i < 10; i++) {
  str += 'hello'
}

test('base', function (t, done) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(__dirname, 'to-file.js'),
    workerData: { dest }
  })
  let runs = 0
  function benchThreadStream () {
    if (++runs === 1000) {
      stream.end()
      return
    }

    for (let i = 0; i < MAX; i++) {
      stream.write(str)
    }
    setImmediate(benchThreadStream)
  }
  benchThreadStream()
  stream.on('finish', function () {
    done()
  })
})
