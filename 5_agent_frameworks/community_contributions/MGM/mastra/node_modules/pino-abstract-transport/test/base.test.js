'use strict'

const test = require('node:test')
const assert = require('node:assert')
const { once } = require('node:events')
const { Transform, pipeline } = require('node:stream')
const tspl = require('@matteo.collina/tspl')

const match = require('./match')
const build = require('../')

test('parse newlined delimited JSON', async (t) => {
  const plan = tspl(t, { plan: 2 })
  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      match(expected.shift(), line, { assert: plan })
    })
  })

  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('parse newline delimited JSON', async (t) => {
  const plan = tspl(t, { plan: 2 })
  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      match(expected.shift(), line, { assert: plan })
    })
  }, { parse: 'json' })

  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()
})

test('null support', async (t) => {
  const plan = tspl(t, { plan: 1 })
  const stream = build(function (source) {
    source.on('unknown', function (line) {
      match('null', line, { assert: plan })
    })
  })

  stream.write('null\n')
  stream.end()

  await plan
})

test('broken json', async (t) => {
  const plan = tspl(t, { plan: 2 })
  const expected = '{ "truncated'
  const stream = build(function (source) {
    source.on('unknown', function (line, error) {
      match(expected, line, { assert: plan })
      const regex = /^(Unexpected end of JSON input|Unterminated string in JSON at position 12)( \(line 1 column 13\))?$/
      plan.match(error.message, regex)
    })
  })

  stream.write(expected + '\n')
  stream.end()

  await plan
})

test('pure values', async (t) => {
  const plan = tspl(t, { plan: 3 })
  const stream = build(function (source) {
    source.on('data', function (line) {
      plan.equal(line.data, 42)
      plan.ok(line.time)
      plan.equal(new Date(line.time).getTime(), line.time)
    })
  })

  stream.write('42\n')
  stream.end()

  await plan
})

test('support async iteration', async (t) => {
  const plan = tspl(t, { plan: 2 })
  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(async function (source) {
    for await (const line of source) {
      match(expected.shift(), line, { assert: plan })
    }
  })

  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('rejecting errors the stream', async () => {
  const stream = build(async function (source) {
    throw new Error('kaboom')
  })

  const [err] = await once(stream, 'error')
  assert.equal(err.message, 'kaboom')
})

test('emits an error if the transport expects pino to send the config, but pino is not going to', async function () {
  const stream = build(() => {}, { expectPinoConfig: true })
  const [err] = await once(stream, 'error')
  assert.equal(err.message, 'This transport is not compatible with the current version of pino. Please upgrade pino to the latest version.')
})

test('set metadata', async (t) => {
  const plan = tspl(t, { plan: 9 })

  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      const obj = expected.shift()
      plan.equal(this.lastLevel, obj.level)
      plan.equal(this.lastTime, obj.time)
      match(this.lastObj, obj, { assert: plan })
      match(obj, line, { assert: plan })
    })
  }, { metadata: true })

  plan.equal(stream[Symbol.for('pino.metadata')], true)
  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('parse lines', async (t) => {
  const plan = tspl(t, { plan: 9 })

  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      const obj = expected.shift()
      plan.equal(this.lastLevel, obj.level)
      plan.equal(this.lastTime, obj.time)
      match(this.lastObj, obj, { assert: plan })
      match(JSON.stringify(obj), line, { assert: plan })
    })
  }, { metadata: true, parse: 'lines' })

  plan.equal(stream[Symbol.for('pino.metadata')], true)
  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('custom parse line function', async (t) => {
  const plan = tspl(t, { plan: 11 })

  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]
  let num = 0

  function parseLine (str) {
    const obj = JSON.parse(str)
    match(expected[num], obj, { assert: plan })
    return obj
  }

  const stream = build(function (source) {
    source.on('data', function (line) {
      const obj = expected[num]
      plan.equal(this.lastLevel, obj.level)
      plan.equal(this.lastTime, obj.time)
      match(this.lastObj, obj, { assert: plan })
      match(obj, line, { assert: plan })
      num++
    })
  }, { metadata: true, parseLine })

  plan.equal(stream[Symbol.for('pino.metadata')], true)
  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('set metadata (default)', async (t) => {
  const plan = tspl(t, { plan: 9 })

  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      const obj = expected.shift()
      plan.equal(this.lastLevel, obj.level)
      plan.equal(this.lastTime, obj.time)
      match(this.lastObj, obj, { assert: plan })
      match(obj, line, { assert: plan })
    })
  })

  plan.equal(stream[Symbol.for('pino.metadata')], true)
  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('do not set metadata', async (t) => {
  const plan = tspl(t, { plan: 9 })

  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      const obj = expected.shift()
      plan.equal(this.lastLevel, undefined)
      plan.equal(this.lastTime, undefined)
      plan.equal(this.lastObj, undefined)
      match(obj, line, { assert: plan })
    })
  }, { metadata: false })

  plan.equal(stream[Symbol.for('pino.metadata')], undefined)
  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('close logic', async (t) => {
  const plan = tspl(t, { plan: 3 })
  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      match(expected.shift(), line, { assert: plan })
    })
  }, {
    close (err, cb) {
      plan.ok('close called')
      process.nextTick(cb, err)
    }
  })

  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('close with promises', async (t) => {
  const plan = tspl(t, { plan: 3 })
  const expected = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const stream = build(function (source) {
    source.on('data', function (line) {
      match(expected.shift(), line, { assert: plan })
    })
  }, {
    async close () {
      plan.ok('close called')
    }
  })

  const lines = expected.map(JSON.stringify).join('\n')
  stream.write(lines)
  stream.end()

  await plan
})

test('support Transform streams', async (t) => {
  const plan = tspl(t, { plan: 7 })

  const expected1 = [{
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'hello world'
  }, {
    level: 30,
    time: 1617955768092,
    pid: 2942,
    hostname: 'MacBook-Pro.local',
    msg: 'another message',
    prop: 42
  }]

  const expected2 = []

  const stream1 = build(function (source) {
    const transform = new Transform({
      objectMode: true,
      autoDestroy: true,
      transform (chunk, enc, cb) {
        match(expected1.shift(), chunk, { assert: plan })
        chunk.service = 'from transform'
        expected2.push(chunk)
        cb(null, JSON.stringify(chunk) + '\n')
      }
    })

    pipeline(source, transform, () => {})

    return transform
  }, { enablePipelining: true })

  const stream2 = build(function (source) {
    source.on('data', function (line) {
      match(expected2.shift(), line, { assert: plan })
    })
  })

  pipeline(stream1, stream2, function (err) {
    plan.equal(err, undefined)
    plan.deepStrictEqual(expected1, [])
    plan.deepStrictEqual(expected2, [])
  })

  const lines = expected1.map(JSON.stringify).join('\n')
  stream1.write(lines)
  stream1.end()

  await plan
})
