import { describe, expect, it } from '@jest/globals'
import {
  buildSurveyResponseProperties,
  getSurveyInteractionProperty,
  getSurveyResponseKey,
  getSurveyResponseValue,
  surveyHasResponses,
} from './events'

describe('survey event helpers', () => {
  const survey = {
    id: 'survey-1',
    current_iteration: 2,
    questions: [
      { id: 'q1', question: 'Rate us', originalQuestionIndex: 0 },
      { id: 'q2', question: 'Anything else?', originalQuestionIndex: 1 },
    ],
  }

  it('builds response properties with current and legacy response keys', () => {
    const responses = {
      [getSurveyResponseKey('q1')]: 5,
      [getSurveyResponseKey('q2')]: ['fast', 'clear'],
    }

    expect(buildSurveyResponseProperties(responses, survey)).toEqual({
      $survey_questions: [
        { id: 'q1', question: 'Rate us', response: 5 },
        { id: 'q2', question: 'Anything else?', response: ['fast', 'clear'] },
      ],
      $survey_response_q1: 5,
      $survey_response_q2: ['fast', 'clear'],
      $survey_response: 5,
      $survey_response_1: ['fast', 'clear'],
    })
  })

  it('copies array response values before returning them', () => {
    const responses = { [getSurveyResponseKey('q1')]: ['a'] }

    const response = getSurveyResponseValue(responses, 'q1')

    expect(response).toEqual(['a'])
    expect(response).not.toBe(responses.$survey_response_q1)
  })

  it('detects non-nullish responses and builds interaction property names', () => {
    expect(surveyHasResponses({ $survey_response_q1: null })).toBe(false)
    expect(surveyHasResponses({ $survey_response_q1: 0 })).toBe(true)
    expect(getSurveyInteractionProperty(survey, 'responded')).toBe('$survey_responded/survey-1/2')
  })
})
