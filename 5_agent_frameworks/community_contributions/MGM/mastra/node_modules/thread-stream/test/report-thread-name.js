'use strict'

const { Writable } = require('stream')
const { threadName, parentPort } = require('worker_threads')

module.exports = function () {
  parentPort.once('message', function ({ port }) {
    port.postMessage({ threadName })
  })

  return new Writable({
    write (chunk, encoding, callback) {
      callback()
    }
  })
}
