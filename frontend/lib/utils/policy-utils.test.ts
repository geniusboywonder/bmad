import { describe, it, expect } from 'vitest';

import { buildPolicyGuidance } from './policy-utils';

describe('buildPolicyGuidance', () => {
  it('normalizes policy decision objects', () => {
    const payload = {
      detail: {
        message: "Agent 'coder' is not allowed in the 'discovery' phase.",
        policy_decision: {
          reason_code: 'AGENT_NOT_ALLOWED',
          allowed_agents: ['analyst'],
          current_phase: 'discovery',
        },
      },
    };

    const guidance = buildPolicyGuidance(payload, 'fallback');

    expect(guidance).toEqual(
      expect.objectContaining({
        status: 'denied',
        reasonCode: 'AGENT_NOT_ALLOWED',
        message: "Agent 'coder' is not allowed in the 'discovery' phase.",
        currentPhase: 'discovery',
        allowedAgents: ['analyst'],
      })
    );
    expect(guidance?.timestamp).toBeTruthy();
  });

  it('marks prompt mismatches as needs clarification', () => {
    const payload = {
      detail: {
        message: 'Instructions do not match the current phase.',
        policy_decision: {
          reason_code: 'PROMPT_MISALIGNED',
          allowed_agents: ['analyst'],
          current_phase: 'discovery',
        },
      },
    };

    const guidance = buildPolicyGuidance(payload, 'fallback');

    expect(guidance).toMatchObject({
      status: 'needs_clarification',
      reasonCode: 'PROMPT_MISALIGNED',
      currentPhase: 'discovery',
      allowedAgents: ['analyst'],
    });
  });

  it('falls back to string detail when structured data missing', () => {
    const guidance = buildPolicyGuidance({ detail: "Agent not permitted in this phase." }, '');

    expect(guidance).toMatchObject({
      status: 'denied',
      message: "Agent not permitted in this phase.",
      allowedAgents: [],
    });
  });
});
