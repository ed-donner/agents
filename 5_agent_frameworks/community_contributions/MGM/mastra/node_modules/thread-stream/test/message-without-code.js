'use strict'

const { Writable } = require('stream')
const { parentPort } = require('worker_threads')

async function run () {
  parentPort.postMessage({
    internal: 'watch-mode'
  })

  return new Writable({
    autoDestroy: true,
    write (chunk, enc, cb) {
      cb()
    }
  })
}

module.exports = run
