import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AgentStatusCard, type Agent } from './agent-status-card';

// Mock the websocketService used by the component
vi.mock('@/lib/services/websocket/websocket-service', () => ({
  websocketService: {
    sendAgentCommand: vi.fn(),
  },
}));

const mockAgent: Agent = {
  id: 'agent-1',
  name: 'Analyst Agent',
  role: 'Requirements Analysis',
  status: 'idle',
  lastActivity: new Date().toISOString(),
  tasksCompleted: 5,
  successRate: 95,
  is_thinking: false,
};

describe('AgentStatusCard Component', () => {
  it('should render the agent name', () => {
    render(<AgentStatusCard agent={mockAgent} />);
    expect(screen.getByText('Analyst Agent')).toBeInTheDocument();
  });

  it('should display "Queued" status for idle agent', () => {
    const idleAgent = { ...mockAgent, status: 'idle' as const };
    render(<AgentStatusCard agent={idleAgent} />);
    expect(screen.getByText('Queued')).toBeInTheDocument();
  });

  it('should display "WIP" status for working agent', () => {
    const workingAgent = { ...mockAgent, status: 'working' as const, currentTask: 'Analyzing prompt' };
    render(<AgentStatusCard agent={workingAgent} />);
    expect(screen.getByText('WIP')).toBeInTheDocument();
    expect(screen.getByText('Analyzing prompt')).toBeInTheDocument();
  });

  it('should display task progress when available', () => {
    const progressAgent = { ...mockAgent, status: 'working' as const, progress_current: 2, progress_total: 5 };
    render(<AgentStatusCard agent={progressAgent} />);
    expect(screen.getByText('Task: 2/5')).toBeInTheDocument();
  });

  it('should display "Error" status correctly', () => {
    const errorAgent = { ...mockAgent, status: 'error' as const };
    render(<AgentStatusCard agent={errorAgent} />);
    const errorBadge = screen.getByText('Error');
    expect(errorBadge).toBeInTheDocument();
    expect(errorBadge).toHaveClass('bg-red-500');
  });

  it('should show play icon when paused', () => {
    const pausedAgent = { ...mockAgent, status: 'paused' as const };
    render(<AgentStatusCard agent={pausedAgent} />);
    // The button has a Play icon, which doesn't have text. We can check for the button's presence.
    // A better way would be to have a data-testid on the icon itself.
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
