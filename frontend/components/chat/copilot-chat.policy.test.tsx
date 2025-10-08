import { beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import CustomCopilotChat from './copilot-chat';
import { useAppStore } from '@/lib/stores/app-store';
import { useHITLStore } from '@/lib/stores/hitl-store';

const initialStoreState = useAppStore.getState();
const initialHitlState = useHITLStore.getState();

describe('CustomCopilotChat policy gating', () => {
  beforeAll(() => {
    if (!HTMLElement.prototype.scrollIntoView) {
      HTMLElement.prototype.scrollIntoView = () => {};
    }
  });

  beforeEach(() => {
    useAppStore.setState(initialStoreState, true);
    useHITLStore.setState(initialHitlState, true);
    useHITLStore.setState({ loadSettings: async () => {} });
  });

  it('disables chat input and shows blocked placeholder when policy denies agent', () => {
    const timestamp = new Date().toISOString();

    useAppStore.setState({
      policyGuidance: {
        status: 'denied',
        reasonCode: 'AGENT_NOT_ALLOWED',
        message: 'Agent not permitted in this phase.',
        currentPhase: 'discovery',
        allowedAgents: ['analyst'],
        timestamp,
      },
    });

    render(<CustomCopilotChat projectId="proj-1" />);

    const input = screen.getByPlaceholderText(/Select an allowed agent/i);
    expect(input).toBeDisabled();
  });

  it('keeps chat input enabled and suggests clarification when prompt mismatch occurs', () => {
    const timestamp = new Date().toISOString();

    useAppStore.setState({
      policyGuidance: {
        status: 'needs_clarification',
        reasonCode: 'PROMPT_MISALIGNED',
        message: 'Clarify instructions for the current phase.',
        currentPhase: 'discovery',
        allowedAgents: ['analyst'],
        timestamp,
      },
    });

    render(<CustomCopilotChat projectId="proj-1" />);

    const input = screen.getByPlaceholderText(/Clarify instructions/i);
    expect(input).not.toBeDisabled();
  });
});
