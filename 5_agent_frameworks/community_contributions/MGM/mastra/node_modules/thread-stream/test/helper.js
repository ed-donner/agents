'use strict'

const { join } = require('path')
const { tmpdir } = require('os')
const { unlinkSync } = require('fs')

const files = []
let count = 0

function file () {
  const file = join(tmpdir(), `thread-stream-${process.pid}-${count++}`)
  files.push(file)
  return file
}

process.on('beforeExit', () => {
  for (const file of files) {
    try {
      unlinkSync(file)
    } catch (e) {
      // ignore cleanup errors
    }
  }
})

module.exports.file = file
