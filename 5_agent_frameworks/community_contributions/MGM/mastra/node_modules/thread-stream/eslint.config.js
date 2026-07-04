'use strict'

const neostandard = require('neostandard')

module.exports = neostandard({
  ignores: [
    'test/ts/**/*',
    'test/syntax-error.mjs'
  ]
})
