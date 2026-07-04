'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const { join } = require('path')
const { file } = require('./helper')
const ThreadStream = require('..')

function basic (esVersion) {
  test(`transpiled-ts-to-${esVersion}`, function () {
    const dest = file()
    const stream = new ThreadStream({
      filename: join(__dirname, 'ts', `to-file.${esVersion}.cjs`),
      workerData: { dest },
      sync: true
    })

    // There are arbitrary checks, the important aspect of this test is to ensure
    // that we can properly load the transpiled file into our worker thread.
    assert.deepStrictEqual(stream.writableEnded, false)
    stream.end()
    assert.deepStrictEqual(stream.writableEnded, true)
  })
}

basic('es5')
basic('es6')
basic('es2017')
basic('esnext')
