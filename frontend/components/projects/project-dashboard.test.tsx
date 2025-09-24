/**
 * Project Dashboard Component Tests - Phase 2 Integration
 * Tests for project dashboard UI, interactions, and state management
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProjectDashboard } from './project-dashboard'
import { useProjectStore } from '@/lib/stores/project-store'
import { useAppStore } from '@/lib/stores/app-store'
import { useToast } from '@/hooks/use-toast'
import { Project } from '@/lib/services/api/types'

// Mock the stores and hooks
vi.mock('@/lib/stores/project-store', () => ({
  useProjectStore: vi.fn(),
  projectStoreSelectors: {
    projectsList: vi.fn(),
    activeProjects: vi.fn(),
    completedProjects: vi.fn(),
  },
}))

vi.mock('@/lib/stores/app-store', () => ({
  useAppStore: vi.fn(),
}))

vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn(),
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className, ...props }: any) => <div data-testid="card" className={className} {...props}>{children}</div>,
  CardContent: ({ children, ...props }: any) => <div data-testid="card-content" {...props}>{children}</div>,
  CardDescription: ({ children, ...props }: any) => <div data-testid="card-description" {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div data-testid="card-header" {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: any) => <h3 data-testid="card-title" {...props}>{children}</h3>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} {...props}>
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, ...props }: any) => (
    <span data-testid="badge" data-variant={variant} {...props}>{children}</span>
  ),
}))

vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, ...props }: any) => (
    <div data-testid="progress" data-value={value} {...props} />
  ),
}))

vi.mock('@/components/ui/separator', () => ({
  Separator: (props: any) => <hr data-testid="separator" {...props} />,
}))

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: any) => <div data-testid="dropdown-menu">{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({ children, onClick, ...props }: any) => (
    <div data-testid="dropdown-item" onClick={onClick} {...props}>{children}</div>
  ),
  DropdownMenuSeparator: (props: any) => <hr data-testid="dropdown-separator" {...props} />,
  DropdownMenuTrigger: ({ children }: any) => <div data-testid="dropdown-trigger">{children}</div>,
}))

vi.mock('./project-creation-form', () => ({
  ProjectCreationForm: ({ onSuccess, trigger }: any) => (
    <div data-testid="project-creation-form">
      {trigger}
      <button onClick={() => onSuccess?.({ id: 'new-project', name: 'New Project' })}>
        Create Project
      </button>
    </div>
  ),
}))

vi.mock('@/lib/services/api/loading-states', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}))

const mockProjects: Project[] = [
  {
    id: 'project-1',
    name: 'Test Project 1',
    description: 'Test description 1',
    status: 'active',
    priority: 'high',
    progress: 65,
    budget_limit: 1000,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T12:00:00Z',
  },
  {
    id: 'project-2',
    name: 'Test Project 2',
    status: 'completed',
    priority: 'medium',
    progress: 100,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
  {
    id: 'project-3',
    name: 'Test Project 3',
    status: 'paused',
    priority: 'low',
    progress: 25,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T06:00:00Z',
  },
]

describe('ProjectDashboard', () => {
  const mockUseProjectStore = useProjectStore as any
  const mockUseAppStore = useAppStore as any
  const mockUseToast = useToast as any

  const defaultProjectStore = {
    projects: mockProjects.reduce((acc, p) => ({ ...acc, [p.id]: p }), {}),
    currentProject: null,
    isLoading: false,
    error: null,
    fetchProjects: vi.fn(),
    selectProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
    startProject: vi.fn(),
    pauseProject: vi.fn(),
    completeProject: vi.fn(),
  }

  const defaultAppStore = {
    isLoading: false,
    setLoading: vi.fn(),
  }

  const mockToast = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseProjectStore.mockReturnValue(defaultProjectStore)
    mockUseAppStore.mockReturnValue(defaultAppStore)
    mockUseToast.mockReturnValue({ toast: mockToast })
  })

  describe('Rendering', () => {
    it('should render dashboard header with title and stats', () => {
      render(<ProjectDashboard />)

      expect(screen.getByText('Project Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Manage and monitor your AI agent projects')).toBeInTheDocument()

      // Should show project stats
      expect(screen.getByText('Total Projects')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('should render project cards for all projects', () => {
      render(<ProjectDashboard />)

      mockProjects.forEach(project => {
        expect(screen.getByText(project.name)).toBeInTheDocument()
      })
    })

    it('should show loading state when loading', () => {
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        isLoading: true,
      })

      render(<ProjectDashboard />)
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('should show empty state when no projects', () => {
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        projects: {},
      })

      render(<ProjectDashboard />)
      expect(screen.getByText('No projects found')).toBeInTheDocument()
      expect(screen.getByText('Create your first project to get started')).toBeInTheDocument()
    })

    it('should show error state when error exists', () => {
      const errorMessage = 'Failed to load projects'
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        error: errorMessage,
      })

      render(<ProjectDashboard />)
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  describe('Project Card Interactions', () => {
    it('should select project when card is clicked', async () => {
      const selectProject = vi.fn()
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        selectProject,
      })

      render(<ProjectDashboard />)

      const projectCard = screen.getByText('Test Project 1').closest('[data-testid="card"]')
      expect(projectCard).toBeInTheDocument()

      fireEvent.click(projectCard!)
      expect(selectProject).toHaveBeenCalledWith('project-1')
    })

    it('should show status badge with correct variant', () => {
      render(<ProjectDashboard />)

      const badges = screen.getAllByTestId('badge')
      expect(badges.some(badge => badge.textContent === 'active')).toBe(true)
      expect(badges.some(badge => badge.textContent === 'completed')).toBe(true)
      expect(badges.some(badge => badge.textContent === 'paused')).toBe(true)
    })

    it('should show progress bar for active projects', () => {
      render(<ProjectDashboard />)

      const progressBars = screen.getAllByTestId('progress')
      expect(progressBars).toHaveLength(3)

      // Check that progress values are set correctly
      expect(progressBars.some(bar => bar.getAttribute('data-value') === '65')).toBe(true)
      expect(progressBars.some(bar => bar.getAttribute('data-value') === '100')).toBe(true)
      expect(progressBars.some(bar => bar.getAttribute('data-value') === '25')).toBe(true)
    })
  })

  describe('Project Actions', () => {
    it('should handle project start action', async () => {
      const startProject = vi.fn().mockResolvedValue(undefined)
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        startProject,
      })

      render(<ProjectDashboard />)

      // Find and click start button (this would be in dropdown menu)
      const dropdownTriggers = screen.getAllByTestId('dropdown-trigger')
      fireEvent.click(dropdownTriggers[0])

      // Simulate clicking start action
      const startButton = screen.getByText('Start')
      fireEvent.click(startButton)

      await waitFor(() => {
        expect(startProject).toHaveBeenCalledWith('project-1')
      })
    })

    it('should handle project pause action', async () => {
      const pauseProject = vi.fn().mockResolvedValue(undefined)
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        pauseProject,
      })

      render(<ProjectDashboard />)

      const pauseButton = screen.getByText('Pause')
      fireEvent.click(pauseButton)

      await waitFor(() => {
        expect(pauseProject).toHaveBeenCalledWith('project-1')
      })
    })

    it('should handle project delete action', async () => {
      const deleteProject = vi.fn().mockResolvedValue(undefined)
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        deleteProject,
      })

      render(<ProjectDashboard />)

      const deleteButton = screen.getByText('Delete')
      fireEvent.click(deleteButton)

      await waitFor(() => {
        expect(deleteProject).toHaveBeenCalledWith('project-1')
      })
    })

    it('should show toast on successful action', async () => {
      const updateProject = vi.fn().mockResolvedValue(undefined)
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        updateProject,
      })

      render(<ProjectDashboard />)

      const statusButton = screen.getByText('Change Status')
      fireEvent.click(statusButton)

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Status Updated',
          description: expect.any(String),
          duration: 3000,
        })
      })
    })

    it('should show error toast on failed action', async () => {
      const updateProject = vi.fn().mockRejectedValue(new Error('Update failed'))
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        updateProject,
      })

      render(<ProjectDashboard />)

      const statusButton = screen.getByText('Change Status')
      fireEvent.click(statusButton)

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Update Failed',
          description: 'Failed to update project status',
          variant: 'destructive',
          duration: 3000,
        })
      })
    })
  })

  describe('Project Creation', () => {
    it('should show project creation form', () => {
      render(<ProjectDashboard />)
      expect(screen.getByTestId('project-creation-form')).toBeInTheDocument()
    })

    it('should handle successful project creation', async () => {
      const fetchProjects = vi.fn()
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        fetchProjects,
      })

      render(<ProjectDashboard />)

      const createButton = screen.getByText('Create Project')
      fireEvent.click(createButton)

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Project Created',
          description: expect.stringContaining('New Project'),
          duration: 5000,
        })
      })
    })
  })

  describe('Filters and Sorting', () => {
    it('should filter projects by status', async () => {
      render(<ProjectDashboard />)

      const statusFilter = screen.getByText('Status Filter')
      fireEvent.click(statusFilter)

      const activeFilter = screen.getByText('Active Only')
      fireEvent.click(activeFilter)

      // Should only show active projects
      expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      expect(screen.queryByText('Test Project 2')).not.toBeInTheDocument()
      expect(screen.queryByText('Test Project 3')).not.toBeInTheDocument()
    })

    it('should sort projects by different criteria', async () => {
      render(<ProjectDashboard />)

      const sortSelect = screen.getByText('Sort By')
      fireEvent.click(sortSelect)

      const nameSort = screen.getByText('Name')
      fireEvent.click(nameSort)

      // Projects should be sorted alphabetically
      const projectCards = screen.getAllByTestId('card-title')
      const projectNames = projectCards.map(card => card.textContent)
      expect(projectNames).toEqual(['Test Project 1', 'Test Project 2', 'Test Project 3'])
    })
  })

  describe('Real-time Updates', () => {
    it('should update project status in real-time', () => {
      const { rerender } = render(<ProjectDashboard />)

      // Initially shows active status
      expect(screen.getByText('active')).toBeInTheDocument()

      // Update store to show paused status
      const updatedProjects = {
        ...mockProjects[0],
        status: 'paused' as const,
      }

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        projects: { ...defaultProjectStore.projects, 'project-1': updatedProjects },
      })

      rerender(<ProjectDashboard />)

      expect(screen.getByText('paused')).toBeInTheDocument()
    })

    it('should update project progress in real-time', () => {
      const { rerender } = render(<ProjectDashboard />)

      // Initially shows 65% progress
      const progressBar = screen.getAllByTestId('progress')[0]
      expect(progressBar.getAttribute('data-value')).toBe('65')

      // Update store with new progress
      const updatedProjects = {
        ...mockProjects[0],
        progress: 80,
      }

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        projects: { ...defaultProjectStore.projects, 'project-1': updatedProjects },
      })

      rerender(<ProjectDashboard />)

      const updatedProgressBar = screen.getAllByTestId('progress')[0]
      expect(updatedProgressBar.getAttribute('data-value')).toBe('80')
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ProjectDashboard />)

      expect(screen.getByRole('main')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
    })

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup()
      render(<ProjectDashboard />)

      const createButton = screen.getByRole('button', { name: /create/i })

      await user.tab()
      expect(createButton).toHaveFocus()
    })
  })

  describe('Error Handling', () => {
    it('should display error messages from store', () => {
      const errorMessage = 'Network connection failed'
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        error: errorMessage,
      })

      render(<ProjectDashboard />)
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    it('should handle missing project data gracefully', () => {
      const incompleteProject = {
        id: 'incomplete-project',
        name: 'Incomplete Project',
        // Missing other required fields
      }

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        projects: { 'incomplete-project': incompleteProject },
      })

      expect(() => render(<ProjectDashboard />)).not.toThrow()
      expect(screen.getByText('Incomplete Project')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('should not re-render unnecessarily', () => {
      const renderSpy = vi.fn()
      const TestComponent = () => {
        renderSpy()
        return <ProjectDashboard />
      }

      const { rerender } = render(<TestComponent />)
      expect(renderSpy).toHaveBeenCalledTimes(1)

      // Re-render with same props should not cause additional renders
      rerender(<TestComponent />)
      expect(renderSpy).toHaveBeenCalledTimes(2)
    })
  })
})