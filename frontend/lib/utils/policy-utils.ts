import type { AgentType } from '@/lib/services/api/types';
import type { PolicyGuidance } from '@/lib/stores/app-store';

/**
 * Normalize backend policy responses into a shared PolicyGuidance shape.
 */
export function buildPolicyGuidance(payload: any, fallbackMessage: string): PolicyGuidance | null {
  if (!payload && !fallbackMessage) {
    return null;
  }

  const detail = payload?.detail ?? payload;
  const policySource = detail?.policy_decision ?? detail;

  if (policySource && typeof policySource === 'object') {
    const reasonCode: string | undefined =
      policySource.reason_code || policySource.reasonCode;

    const message: string =
      detail?.message ||
      policySource.message ||
      policySource.remediation ||
      fallbackMessage;

    if (!reasonCode) {
      return null;
    }

    const allowedAgents: AgentType[] = Array.isArray(policySource.allowed_agents || policySource.allowedAgents)
      ? (policySource.allowed_agents || policySource.allowedAgents)
      : [];

    const currentPhase: string | undefined =
      policySource.current_phase || policySource.currentPhase;

    const status: PolicyGuidance['status'] =
      reasonCode === 'PROMPT_MISALIGNED' ? 'needs_clarification' : 'denied';

    return {
      status,
      reasonCode,
      message,
      currentPhase,
      allowedAgents,
      timestamp: new Date().toISOString(),
    };
  }

  if (typeof detail === 'string') {
    return {
      status: 'denied',
      reasonCode: 'POLICY_ENFORCED',
      message: detail,
      currentPhase: undefined,
      allowedAgents: [],
      timestamp: new Date().toISOString(),
    };
  }

  if (fallbackMessage) {
    return {
      status: 'denied',
      reasonCode: 'POLICY_ENFORCED',
      message: fallbackMessage,
      currentPhase: undefined,
      allowedAgents: [],
      timestamp: new Date().toISOString(),
    };
  }

  return null;
}
