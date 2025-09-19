import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Sidebar } from './sidebar';
import { usePathname } from 'next/navigation';

// Mock the next/navigation module
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(),
}));

// Mock the SystemHealthDashboard component as it's a complex child component
vi.mock('./system-health-dashboard', () => ({
  SystemHealthDashboard: () => <div data-testid="system-health-dashboard-mock" />,
}));

vi.mock('./services-status', () => ({
    ServicesStatus: () => <div data-testid="services-status-mock" />,
}));

vi.mock('./connection-status', () => ({
    ConnectionStatus: () => <div data-testid="connection-status-mock" />,
}));

const mockOnViewChange = vi.fn();

describe('Sidebar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render all navigation items', () => {
    // Arrange
    (usePathname as vi.Mock).mockReturnValue('/');
    render(<Sidebar activeView="dashboard" onViewChange={mockOnViewChange} />);

    // Assert
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Requirements')).toBeInTheDocument();
    expect(screen.getByText('Design')).toBeInTheDocument();
    expect(screen.getByText('Dev')).toBeInTheDocument();
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('Deploy')).toBeInTheDocument();
    expect(screen.getByText('Logs')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('should highlight the active link based on the current pathname', () => {
    // Arrange
    (usePathname as vi.Mock).mockReturnValue('/logs');
    render(<Sidebar activeView="logs" onViewChange={mockOnViewChange} />);

    // Act
    const logsLink = screen.getByRole('link', { name: /Logs/i });
    const dashboardLink = screen.getByRole('link', { name: /Dashboard/i });

    // Assert
    expect(logsLink.querySelector('button')).toHaveClass(/bg-primary\/10/);
    expect(dashboardLink.querySelector('button')).not.toHaveClass(/bg-primary\/10/);
  });

  it('should call onViewChange when a navigation item is clicked', async () => {
    // Arrange
    (usePathname as vi.Mock).mockReturnValue('/');
    render(<Sidebar activeView="dashboard" onViewChange={mockOnViewChange} />);
    const requirementsButton = screen.getByRole('button', { name: /Requirements/i });

    // Act
    await act(async () => {
      fireEvent.click(requirementsButton);
    });

    // Assert
    expect(mockOnViewChange).toHaveBeenCalledWith('Requirements');
  });

  it('should collapse and expand when the chevron button is clicked', async () => {
    // Arrange
    (usePathname as vi.Mock).mockReturnValue('/');
    render(<Sidebar activeView="dashboard" onViewChange={mockOnViewChange} />);

    // Check initial state (expanded)
    expect(screen.getByText('BotArmy')).toBeInTheDocument();

    // Act: Collapse the sidebar
    const collapseButton = screen.getByLabelText('Collapse sidebar');
    await act(async () => {
        fireEvent.click(collapseButton);
    });

    // Assert: Sidebar is collapsed
    expect(screen.queryByText('BotArmy')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Expand sidebar')).toBeInTheDocument();

    // Act: Expand the sidebar
    const expandButton = screen.getByLabelText('Expand sidebar');
    await act(async () => {
        fireEvent.click(expandButton);
    });

    // Assert: Sidebar is expanded again
    expect(screen.getByText('BotArmy')).toBeInTheDocument();
  });
});
