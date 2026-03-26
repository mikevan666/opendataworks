import { describeToolAction, extractToolSkillName } from '../toolPresentation'

describe('toolPresentation', () => {
  it('infers skill traces from generic tool calls when a skill identifier is present', () => {
    const tool = {
      name: 'Tool',
      input: {
        skill: 'architecture-assistant'
      },
      output: 'Launching skill: architecture-assistant'
    }

    expect(extractToolSkillName(tool)).toBe('architecture-assistant')
    expect(describeToolAction(tool).kind).toBe('skill')
    expect(describeToolAction(tool).detail).toBe('architecture-assistant')
  })
})
