/**
 * Project Creation Form Tests - Phase 2 Integration
 * Tests for project creation form validation, submission, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProjectCreationForm } from './project-creation-form'
import { useProjectStore } from '@/lib/stores/project-store'
import { useToast } from '@/hooks/use-toast'

// Mock the stores and hooks
vi.mock('@/lib/stores/project-store', () => ({
  useProjectStore: vi.fn(),
}))

vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn(),
}))

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, type, variant, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled}
      type={type}
      data-variant={variant}
      {...props}
    >
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/input', () => ({
  Input: ({ value, onChange, ...props }: any) => (
    <input
      value={value}
      onChange={onChange}
      {...props}
    />
  ),
}))

vi.mock('@/components/ui/textarea', () => ({
  Textarea: ({ value, onChange, ...props }: any) => (
    <textarea
      value={value}
      onChange={onChange}
      {...props}
    />
  ),
}))

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: any) => <div data-testid="card" {...props}>{children}</div>,
  CardContent: ({ children, ...props }: any) => <div data-testid="card-content" {...props}>{children}</div>,
  CardDescription: ({ children, ...props }: any) => <div data-testid="card-description" {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div data-testid="card-header" {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: any) => <h3 data-testid="card-title" {...props}>{children}</h3>,
}))

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: any) => open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children, ...props }: any) => <div data-testid="dialog-content" {...props}>{children}</div>,
  DialogDescription: ({ children, ...props }: any) => <div data-testid="dialog-description" {...props}>{children}</div>,
  DialogHeader: ({ children, ...props }: any) => <div data-testid="dialog-header" {...props}>{children}</div>,
  DialogTitle: ({ children, ...props }: any) => <h2 data-testid="dialog-title" {...props}>{children}</h2>,
  DialogTrigger: ({ children, onClick }: any) => (
    <div data-testid="dialog-trigger" onClick={onClick}>{children}</div>
  ),
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: any) => (
    <div data-testid="select" data-value={value} onClick={() => onValueChange?.('medium')}>
      {children}
    </div>
  ),
  SelectContent: ({ children }: any) => <div data-testid="select-content">{children}</div>,
  SelectItem: ({ children, value, onClick }: any) => (
    <div data-testid="select-item" data-value={value} onClick={onClick}>{children}</div>
  ),
  SelectTrigger: ({ children }: any) => <div data-testid="select-trigger">{children}</div>,
  SelectValue: ({ placeholder }: any) => <div data-testid="select-value">{placeholder}</div>,
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, onClick, ...props }: any) => (
    <span data-testid="badge" data-variant={variant} onClick={onClick} {...props}>
      {children}
    </span>
  ),
}))

describe('ProjectCreationForm', () => {
  const mockUseProjectStore = useProjectStore as any
  const mockUseToast = useToast as any

  const defaultProjectStore = {
    createProject: vi.fn(),
    isLoading: false,
    error: null,
    clearError: vi.fn(),
  }

  const mockToast = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseProjectStore.mockReturnValue(defaultProjectStore)
    mockUseToast.mockReturnValue({ toast: mockToast })
  })

  describe('Rendering', () => {
    it('should render form with all required fields', () => {
      render(<ProjectCreationForm />)

      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/priority/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/budget limit/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/estimated duration/i)).toBeInTheDocument()
    })

    it('should render with custom trigger element', () => {
      const customTrigger = <button>Custom Create Button</button>
      render(<ProjectCreationForm trigger={customTrigger} />)

      expect(screen.getByText('Custom Create Button')).toBeInTheDocument()
    })

    it('should show form title and description', () => {
      render(<ProjectCreationForm />)

      expect(screen.getByText('Create New Project')).toBeInTheDocument()
      expect(screen.getByText(/Set up a new AI agent project/i)).toBeInTheDocument()
    })

    it('should show default values in form fields', () => {
      render(<ProjectCreationForm />)

      const budgetInput = screen.getByLabelText(/budget limit/i) as HTMLInputElement
      const durationInput = screen.getByLabelText(/estimated duration/i) as HTMLInputElement

      expect(budgetInput.value).toBe('100')
      expect(durationInput.value).toBe('24')
    })
  })

  describe('Form Validation', () => {
    it('should show validation error for empty project name', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const submitButton = screen.getByRole('button', { name: /create project/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Project name is required')).toBeInTheDocument()
      })
    })

    it('should show validation error for name too long', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const nameInput = screen.getByLabelText(/project name/i)
      const longName = 'a'.repeat(101) // Exceeds 100 character limit

      await user.type(nameInput, longName)
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(screen.getByText('Name must be less than 100 characters')).toBeInTheDocument()
      })
    })

    it('should show validation error for negative budget', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const budgetInput = screen.getByLabelText(/budget limit/i)
      await user.clear(budgetInput)
      await user.type(budgetInput, '-50')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(screen.getByText('Budget must be positive')).toBeInTheDocument()
      })
    })

    it('should show validation error for budget too high', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const budgetInput = screen.getByLabelText(/budget limit/i)
      await user.clear(budgetInput)
      await user.type(budgetInput, '15000')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(screen.getByText('Budget limit exceeded')).toBeInTheDocument()
      })
    })

    it('should show validation error for invalid duration', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const durationInput = screen.getByLabelText(/estimated duration/i)
      await user.clear(durationInput)
      await user.type(durationInput, '0')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(screen.getByText('Duration must be at least 1 hour')).toBeInTheDocument()
      })
    })

    it('should show validation error for duration too high', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const durationInput = screen.getByLabelText(/estimated duration/i)
      await user.clear(durationInput)
      await user.type(durationInput, '800')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(screen.getByText('Maximum 720 hours')).toBeInTheDocument()
      })
    })
  })

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      const user = userEvent.setup()
      const createProject = vi.fn().mockResolvedValue({
        id: 'new-project',
        name: 'Test Project',
      })

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm />)

      // Fill in the form
      await user.type(screen.getByLabelText(/project name/i), 'Test Project')
      await user.type(screen.getByLabelText(/description/i), 'Test description')
      await user.clear(screen.getByLabelText(/budget limit/i))
      await user.type(screen.getByLabelText(/budget limit/i), '500')

      // Submit the form
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(createProject).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Project',
            description: 'Test description',
            budget_limit: 500,
            priority: 'medium',
            status: 'pending',
          })
        )
      })
    })

    it('should show success toast on successful submission', async () => {
      const user = userEvent.setup()
      const createProject = vi.fn().mockResolvedValue({
        id: 'new-project',
        name: 'Test Project',
      })

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm />)

      await user.type(screen.getByLabelText(/project name/i), 'Test Project')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Project Created',
          description: 'Project "Test Project" has been created successfully.',
          duration: 5000,
        })
      })
    })

    it('should call onSuccess callback on successful submission', async () => {
      const user = userEvent.setup()
      const onSuccess = vi.fn()
      const newProject = { id: 'new-project', name: 'Test Project' }
      const createProject = vi.fn().mockResolvedValue(newProject)

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm onSuccess={onSuccess} />)

      await user.type(screen.getByLabelText(/project name/i), 'Test Project')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(newProject)
      })
    })

    it('should reset form on successful submission', async () => {
      const user = userEvent.setup()
      const createProject = vi.fn().mockResolvedValue({
        id: 'new-project',
        name: 'Test Project',
      })

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm />)

      const nameInput = screen.getByLabelText(/project name/i) as HTMLInputElement
      await user.type(nameInput, 'Test Project')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(nameInput.value).toBe('')
      })
    })

    it('should handle submission failure', async () => {
      const user = userEvent.setup()
      const createProject = vi.fn().mockResolvedValue(null)

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm />)

      await user.type(screen.getByLabelText(/project name/i), 'Test Project')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(createProject).toHaveBeenCalled()
        expect(mockToast).not.toHaveBeenCalled()
      })
    })
  })

  describe('Tags Management', () => {
    it('should add tags to project', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const tagInput = screen.getByPlaceholderText(/add tag/i)
      await user.type(tagInput, 'ai')
      await user.press('Enter')

      expect(screen.getByText('ai')).toBeInTheDocument()
    })

    it('should remove tags when clicked', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      // Add a tag
      const tagInput = screen.getByPlaceholderText(/add tag/i)
      await user.type(tagInput, 'ai')
      await user.press('Enter')

      // Remove the tag
      const tagBadge = screen.getByText('ai')
      await user.click(tagBadge)

      expect(screen.queryByText('ai')).not.toBeInTheDocument()
    })

    it('should not add empty tags', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const tagInput = screen.getByPlaceholderText(/add tag/i)
      await user.press('Enter')

      // Should not add any tags
      expect(screen.queryByTestId('badge')).not.toBeInTheDocument()
    })

    it('should not add duplicate tags', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const tagInput = screen.getByPlaceholderText(/add tag/i)

      // Add first tag
      await user.type(tagInput, 'ai')
      await user.press('Enter')

      // Try to add same tag again
      await user.type(tagInput, 'ai')
      await user.press('Enter')

      // Should only have one 'ai' tag
      const aiTags = screen.getAllByText('ai')
      expect(aiTags).toHaveLength(1)
    })
  })

  describe('Priority Selection', () => {
    it('should select different priority levels', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const prioritySelect = screen.getByTestId('select')
      await user.click(prioritySelect)

      expect(prioritySelect.getAttribute('data-value')).toBe('medium')
    })

    it('should show priority badge with correct styling', () => {
      render(<ProjectCreationForm />)

      const priorityBadges = screen.getAllByTestId('badge')
      expect(priorityBadges.some(badge =>
        badge.getAttribute('data-variant')?.includes('medium')
      )).toBe(true)
    })
  })

  describe('Agent Configuration', () => {
    it('should set default agent configuration', async () => {
      const user = userEvent.setup()
      const createProject = vi.fn().mockResolvedValue({
        id: 'new-project',
        name: 'Test Project',
      })

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm />)

      await user.type(screen.getByLabelText(/project name/i), 'Test Project')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(createProject).toHaveBeenCalledWith(
          expect.objectContaining({
            agent_config: {
              max_agents: 3,
              agent_types: ['analyst', 'architect', 'developer'],
            },
          })
        )
      })
    })
  })

  describe('Loading States', () => {
    it('should show loading state during submission', async () => {
      const user = userEvent.setup()
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        isLoading: true,
      })

      render(<ProjectCreationForm />)

      const submitButton = screen.getByRole('button', { name: /create project/i })
      expect(submitButton).toBeDisabled()
      expect(screen.getByTestId('loading-icon')).toBeInTheDocument()
    })

    it('should disable form during loading', () => {
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        isLoading: true,
      })

      render(<ProjectCreationForm />)

      expect(screen.getByLabelText(/project name/i)).toBeDisabled()
      expect(screen.getByLabelText(/description/i)).toBeDisabled()
      expect(screen.getByRole('button', { name: /create project/i })).toBeDisabled()
    })
  })

  describe('Error Handling', () => {
    it('should display error from store', () => {
      const errorMessage = 'Failed to create project'
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        error: errorMessage,
      })

      render(<ProjectCreationForm />)
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    it('should clear error when form is opened', () => {
      const clearError = vi.fn()
      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        error: 'Some error',
        clearError,
      })

      render(<ProjectCreationForm />)

      const triggerButton = screen.getByTestId('dialog-trigger')
      fireEvent.click(triggerButton)

      expect(clearError).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(<ProjectCreationForm />)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create project/i })).toBeInTheDocument()
    })

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      // Tab through form elements
      await user.tab()
      expect(screen.getByLabelText(/project name/i)).toHaveFocus()

      await user.tab()
      expect(screen.getByLabelText(/description/i)).toHaveFocus()
    })

    it('should have proper focus management', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const nameInput = screen.getByLabelText(/project name/i)
      await user.click(nameInput)
      expect(nameInput).toHaveFocus()
    })
  })

  describe('Dialog Management', () => {
    it('should open and close dialog', async () => {
      const user = userEvent.setup()
      render(<ProjectCreationForm />)

      const triggerButton = screen.getByTestId('dialog-trigger')
      await user.click(triggerButton)

      expect(screen.getByTestId('dialog')).toBeInTheDocument()

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(screen.queryByTestId('dialog')).not.toBeInTheDocument()
    })

    it('should close dialog on successful submission', async () => {
      const user = userEvent.setup()
      const createProject = vi.fn().mockResolvedValue({
        id: 'new-project',
        name: 'Test Project',
      })

      mockUseProjectStore.mockReturnValue({
        ...defaultProjectStore,
        createProject,
      })

      render(<ProjectCreationForm />)

      await user.type(screen.getByLabelText(/project name/i), 'Test Project')
      await user.click(screen.getByRole('button', { name: /create project/i }))

      await waitFor(() => {
        expect(screen.queryByTestId('dialog')).not.toBeInTheDocument()
      })
    })
  })
})