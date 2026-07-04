'use strict'

module.exports = match

/**
 * match is a bare-bones object shape matcher. We should be able to replace
 * this with `assert.partialDeepStrictEqual` when v22 is our minimum.
 *
 * @param {object} found
 * @param {object} expected
 */
function match (found, expected, { assert = require('node:assert') } = {}) {
  for (const [key, value] of Object.entries(expected)) {
    if (Object.prototype.toString.call(value) === '[object Object]') {
      match(found[key], value)
      continue
    }
    if (value !== found[key]) {
      throw Error(`expected "${value}" but found "${found[key]}"`)
    }
  }

  assert.ok('passed')
}
