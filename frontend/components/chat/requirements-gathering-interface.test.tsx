import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RequirementsGatheringInterface } from './requirements-gathering-interface';

const mockOnSubmit = vi.fn();

describe('RequirementsGatheringInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render if there are no questions', () => {
    const { container } = render(
      <RequirementsGatheringInterface questions={[]} onSubmit={mockOnSubmit} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render questions and inputs', () => {
    const questions = [{ id: '1', text: 'Question 1?' }];
    render(
      <RequirementsGatheringInterface
        questions={questions}
        onSubmit={mockOnSubmit}
      />,
    );
    expect(screen.getByText('Question 1?')).not.toBeNull();
    expect(screen.getByPlaceholderText('Your answer...')).not.toBeNull();
  });

  it('should call updateAnswer on input change', () => {
    const questions = [{ id: '1', text: 'Question 1?' }];
    render(
      <RequirementsGatheringInterface
        questions={questions}
        onSubmit={mockOnSubmit}
      />,
    );
    const input = screen.getByPlaceholderText('Your answer...');
    fireEvent.change(input, { target: { value: 'My answer' } });
    // The component now manages its own state, so we check the value
    expect((input as HTMLInputElement).value).toBe('My answer');
  });

  it('should call onSubmit with the answers when the form is submitted', () => {
    const questions = [{ id: '1', text: 'Question 1?' }];
    render(
      <RequirementsGatheringInterface
        questions={questions}
        onSubmit={mockOnSubmit}
      />,
    );
    const input = screen.getByPlaceholderText('Your answer...');
    fireEvent.change(input, { target: { value: 'My answer' } });

    const submitButton = screen.getByText('Submit Answers');
    fireEvent.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith({ '1': 'My answer' });
  });
});
