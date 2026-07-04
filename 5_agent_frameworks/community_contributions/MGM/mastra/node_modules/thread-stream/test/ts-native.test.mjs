import { test } from 'node:test'
import assert from 'node:assert'
import { readFile } from 'fs/promises'
import ThreadStream from '../index.js'
import { join } from 'desm'
import { file } from './helper.js'

const nodeVersion = parseInt(process.versions.node.split('.')[0], 10)

// Native TypeScript stripping (--experimental-strip-types) is only available in Node 22.6+
test('typescript module with native type stripping', { skip: nodeVersion < 22 }, async function (t) {
  const dest = file()
  const stream = new ThreadStream({
    filename: join(import.meta.url, 'ts', 'to-file.ts'),
    workerData: { dest },
    workerOpts: {
      execArgv: ['--experimental-strip-types', '--disable-warning=ExperimentalWarning']
    },
    sync: false
  })

  t.after(() => stream.end())

  assert.ok(stream.write('hello world\n'))
  assert.ok(stream.write('something else\n'))

  stream.end()

  await new Promise((resolve) => {
    stream.on('close', resolve)
  })

  const data = await readFile(dest, 'utf8')
  assert.strictEqual(data, 'hello world\nsomething else\n')
})
