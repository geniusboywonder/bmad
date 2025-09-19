import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EnhancedChatInterface } from './enhanced-chat-interface';
import { useConversationStore } from '@/lib/stores/conversation-store';
import { useAgentStore } from '@/lib/stores/agent-store';
import { useChatModeStore } from '@/lib/stores/chat-mode-store';
import { useInteractiveSessionStore } from '@/lib/stores/interactive-session-store';
import { websocketService } from '@/lib/websocket/websocket-service';

// Mock the external dependencies
vi.mock('@/lib/stores/conversation-store');
vi.mock('@/lib/stores/agent-store');
vi.mock('@/lib/stores/chat-mode-store');
vi.mock('@/lib/stores/interactive-session-store');
vi.mock('@/lib/websocket/websocket-service');

describe('EnhancedChatInterface', () => {
  const mockAddMessage = vi.fn();
  const mockClearMessages = vi.fn();
  const mockToggleMessageCollapse = vi.fn();
  const mockSendChatMessage = vi.fn();
  const mockSendApprovalResponse = vi.fn();

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();

    // Setup mock return values for the hooks and service
    (useConversationStore as any).mockReturnValue({
      messages: [
        { id: '1', agent: 'System', type: 'system', content: 'Welcome!', timestamp: new Date() },
        { id: '2', agent: 'User', type: 'user', content: 'Test prompt', timestamp: new Date() },
      ],
      addMessage: mockAddMessage,
      clearMessages: mockClearMessages,
      toggleMessageCollapse: mockToggleMessageCollapse,
    });

    (useAgentStore as any).mockReturnValue({
      agents: [],
    });

    (useChatModeStore as any).mockReturnValue({
      mode: 'general',
      projectContext: null,
      awaitingBrief: false,
      setAwaitingBrief: vi.fn(),
      switchToProjectMode: vi.fn(),
      switchToGeneralMode: vi.fn(),
    });

    (useInteractiveSessionStore as any).mockReturnValue({
      isAwaitingApproval: false,
      setAwaitingApproval: vi.fn(),
    });

    (websocketService as any).sendChatMessage = mockSendChatMessage;
    (websocketService as any).sendApprovalResponse = mockSendApprovalResponse;
    (websocketService as any).getConnectionStatus = vi.fn().mockReturnValue({ connected: true, reconnecting: false });
    // This is the crucial missing mock
    (websocketService as any).onStatusChange = vi.fn().mockReturnValue(vi.fn());
    (websocketService as any).send = vi.fn();
  });

  it('should render the chat logs from the log store', () => {
    // Arrange
    render(<EnhancedChatInterface />);

    // Assert
    expect(screen.getByText('Welcome!')).toBeInTheDocument();
    expect(screen.getByText('Test prompt')).toBeInTheDocument();
  });

  it('should allow the user to type in the input', async () => {
    // Arrange
    render(<EnhancedChatInterface />);
    const input = screen.getByPlaceholderText(/Type a message or 'start project'.../i);

    // Act
    await act(async () => {
        fireEvent.change(input, { target: { value: 'This is a new message.' } });
    });

    // Assert
    expect(input).toHaveValue('This is a new message.');
  });

  it('should call websocketService.sendChatMessage when sending a valid message', async () => {
    // Arrange
    render(<EnhancedChatInterface />);
    const input = screen.getByPlaceholderText(/Type a message or 'start project'.../i);
    const sendButton = screen.getByRole('button', { name: /Send/i });
    const message = 'This is a valid test message.';

    // Act
    await act(async () => {
        fireEvent.change(input, { target: { value: message } });
    });

    // Ensure the button is enabled before clicking
    expect(sendButton).not.toBeDisabled();

    await act(async () => {
        fireEvent.click(sendButton);
    });

    // Assert
    expect(mockAddMessage).toHaveBeenCalledWith(expect.objectContaining({
        agent: 'User',
        content: message,
    }));
    expect(mockSendChatMessage).toHaveBeenCalledWith(message);
  });

  it('should disable the send button for short messages when awaiting brief', async () => {
    // Arrange
    (useChatModeStore as any).mockReturnValue({
      mode: 'general',
      awaitingBrief: true,
      setAwaitingBrief: vi.fn(),
    });
    render(<EnhancedChatInterface />);
    const input = screen.getByPlaceholderText(/Enter project brief.../i);
    const sendButton = screen.getByRole('button', { name: /Send/i });

    // Act
    await act(async () => {
        fireEvent.change(input, { target: { value: 'short' } });
    });

    // Assert
    expect(sendButton).toBeDisabled();
  });

  it('should disable the send button when disconnected', async () => {
    // Arrange
    (websocketService as any).getConnectionStatus = vi.fn().mockReturnValue({ connected: false, reconnecting: false });
    render(<EnhancedChatInterface />);
    const input = screen.getByPlaceholderText(/Connect to server.../i);
    const sendButton = screen.getByRole('button', { name: /Send/i });

    // Assert
    expect(sendButton).toBeDisabled();
    expect(input).toBeDisabled();
  });
});
