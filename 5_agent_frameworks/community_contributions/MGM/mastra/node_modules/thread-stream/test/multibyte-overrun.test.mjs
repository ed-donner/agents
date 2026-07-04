import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import ThreadStream from '../index.js'
import { join } from 'desm'
import { file } from './helper.js'

test('preserves multibyte records that cross the buffer boundary', async () => {
  const dest = file()
  const stream = new ThreadStream({
    bufferSize: 128,
    filename: join(import.meta.url, 'to-file.js'),
    workerData: { dest },
    sync: false
  })

  let expected = ''

  for (let i = 0; i < 1000; i++) {
    const line = `{"idx":${i},"alert":"🚨"}\n`
    expected += line
    stream.write(line)
  }

  await new Promise((resolve, reject) => {
    stream.once('error', reject)
    stream.once('close', resolve)
    stream.end()
  })

  const data = await readFile(dest, 'utf8')
  assert.strictEqual(data, expected)
})
