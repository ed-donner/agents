'use strict'

const { test } = require('node:test')
const assert = require('node:assert')
const indexes = require('../lib/indexes')

for (const index of Object.keys(indexes)) {
  test(`${index} is lock free`, function () {
    assert.strictEqual(Atomics.isLockFree(indexes[index]), true)
  })
}
