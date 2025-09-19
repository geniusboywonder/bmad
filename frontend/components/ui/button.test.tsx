import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Button } from './button';

describe('Button Component', () => {
  it('should render the button with the correct text', () => {
    // Arrange
    const buttonText = 'Click Me';
    render(<Button>{buttonText}</Button>);

    // Act
    const buttonElement = screen.getByRole('button', { name: buttonText });

    // Assert
    expect(buttonElement).toBeInTheDocument();
  });

  it('should apply the correct variant class', () => {
    // Arrange
    const buttonText = 'Destructive Button';
    render(<Button variant="destructive">{buttonText}</Button>);

    // Act
    const buttonElement = screen.getByRole('button', { name: buttonText });

    // Assert
    // We check for a class that is specific to the 'destructive' variant.
    // This is a bit of an implementation detail test, but useful for UI libraries.
    expect(buttonElement).toHaveClass(/bg-destructive/);
  });

  it('should be disabled when the disabled prop is passed', () => {
    // Arrange
    const buttonText = 'Disabled Button';
    render(<Button disabled>{buttonText}</Button>);

    // Act
    const buttonElement = screen.getByRole('button', { name: buttonText });

    // Assert
    expect(buttonElement).toBeDisabled();
  });
});
