import {
  EXCEPTION_STEP_INTERNAL_FIELDS,
  ExceptionStep,
  ExceptionStepsBuffer,
  getUtf8ByteLength,
  resolveExceptionStepsConfig,
  stripReservedExceptionStepFields,
} from './exception-steps'

describe('exception steps', () => {
  describe('resolveExceptionStepsConfig', () => {
    it('uses defaults when no config is passed', () => {
      expect(resolveExceptionStepsConfig()).toEqual({
        enabled: true,
        max_bytes: 32768,
      })
    })

    it('falls back to defaults for invalid values', () => {
      expect(resolveExceptionStepsConfig({ max_bytes: Number.NaN })).toEqual({
        enabled: true,
        max_bytes: 32768,
      })
    })
  })

  describe('stripReservedExceptionStepFields', () => {
    it('strips reserved fields and keeps custom properties', () => {
      const result = stripReservedExceptionStepFields({
        [EXCEPTION_STEP_INTERNAL_FIELDS.MESSAGE]: 'should-strip',
        [EXCEPTION_STEP_INTERNAL_FIELDS.TIMESTAMP]: 'should-strip',
        custom: true,
      })

      expect(result).toEqual({
        sanitizedProperties: { custom: true },
        droppedKeys: [EXCEPTION_STEP_INTERNAL_FIELDS.MESSAGE, EXCEPTION_STEP_INTERNAL_FIELDS.TIMESTAMP],
      })
    })
  })

  describe('ExceptionStepsBuffer', () => {
    const makeStep = (message: string): ExceptionStep => ({
      [EXCEPTION_STEP_INTERNAL_FIELDS.MESSAGE]: message,
      [EXCEPTION_STEP_INTERNAL_FIELDS.TIMESTAMP]: '2026-01-01T00:00:00.000Z',
    })

    const bytesOf = (step: ExceptionStep) => getUtf8ByteLength(JSON.stringify(step))

    it.each([
      {
        desc: 'evicts oldest steps when max bytes are exceeded',
        config: { max_bytes: bytesOf(makeStep('two')) + bytesOf(makeStep('three')) },
        steps: [makeStep('one'), makeStep('two'), makeStep('three')],
        expected: ['two', 'three'],
      },
      {
        desc: 'keeps the most recent step when budget fits only one',
        config: { max_bytes: bytesOf(makeStep('one')) },
        steps: [makeStep('one'), makeStep('two')],
        expected: ['two'],
      },
      {
        desc: 'skips malformed steps that cannot be normalized',
        config: { max_bytes: 10000 },
        steps: [{ $message: '', $timestamp: '2026-01-01T00:00:00.000Z' } as ExceptionStep, makeStep('valid')],
        expected: ['valid'],
      },
      {
        desc: 'drops a step that exceeds the entire budget on its own',
        config: { max_bytes: 10 },
        steps: [makeStep('this message is way too long for the tiny budget')],
        expected: [],
      },
    ])('$desc', ({ config, steps, expected }) => {
      const buffer = new ExceptionStepsBuffer(config)
      for (const step of steps) {
        buffer.add(step)
      }
      expect(buffer.getAttachable().map((s) => s.$message)).toEqual(expected)
    })

    it('clears all steps', () => {
      const buffer = new ExceptionStepsBuffer({ max_bytes: 10000 })
      buffer.add(makeStep('one'))
      buffer.clear()
      expect(buffer.size()).toBe(0)
    })
  })
})
