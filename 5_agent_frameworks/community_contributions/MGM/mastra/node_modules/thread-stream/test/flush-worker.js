'use strict'

const { EventEmitter } = require('events')
const { parentPort } = require('worker_threads')

function createDestination (mode) {
  const destination = new EventEmitter()
  destination.writableEnded = false
  destination.writableNeedDrain = false

  destination.write = function () {
    if (mode === 'drain') {
      destination.writableNeedDrain = true
      setTimeout(() => {
        destination.writableNeedDrain = false
        parentPort.postMessage({
          code: 'EVENT',
          name: 'destination-drain'
        })
        destination.emit('drain')
      }, 50)
    }

    return true
  }

  destination.end = function () {
    destination.writableEnded = true
    destination.emit('close')
  }

  if (mode === 'flush') {
    destination.flush = function (cb) {
      setTimeout(() => {
        parentPort.postMessage({
          code: 'EVENT',
          name: 'destination-flushed'
        })
        cb()
      }, 50)
    }
  }

  if (mode === 'flush-sync') {
    destination.flushSync = function () {
      parentPort.postMessage({
        code: 'EVENT',
        name: 'destination-flush-sync'
      })
    }
  }

  if (mode === 'exit-on-flush') {
    destination.flush = function (_cb) {
      setTimeout(() => {
        process.exit(0)
      }, 20)
    }
  }

  return destination
}

async function run (opts) {
  return createDestination(opts.mode)
}

module.exports = run
