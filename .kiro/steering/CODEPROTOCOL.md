---
inclusion: always
---

# Code Protocol

This document defines the development standards and patterns.

## Architecture Overview

BMad is a full-stack application with:
- **Frontend**: Next.js 14+ with TypeScript, shadcn/ui components, Tailwind CSS
- **Backend**: FastAPI with async patterns, SQLAlchemy, Pydantic models
- **Agent Framework**: Multi-agent orchestration with LLM providers
- **Communication**: WebSocket-based real-time updates

## Development Standards

### Code Quality
- Maximum 600 lines per file
- Single responsibility principle
- Strict TypeScript - avoid `any` types
- Comprehensive error handling and recovery
- Input sanitization and validation
- Accessibility-first design

### Frontend Patterns
- Functional components with hooks
- shadcn/ui component patterns with `@/` imports
- Atomic state updates with proper TypeScript interfaces
- Client-side validation before server requests

### Backend Patterns
- FastAPI async/await patterns
- Pydantic models for all data validation
- InputSanitizer for user inputs
- Connection pooling for LLM providers
- Multi-level rate limiting (IP, user, global)

### Security Requirements
- JSON Schema validation for YAML/configuration files
- Serialization-safe wrappers to prevent circular references
- Security pattern detection and logging
- Comprehensive input validation tests

## Testing Strategy

### Frontend Testing
- **Framework**: Vitest with React Testing Library
- **Setup**: Global configuration in `vitest.setup.ts`
- **Focus**: Component behavior, user interactions, accessibility

### Backend Testing
- **Framework**: pytest with `pytest-asyncio`
- **Setup**: Configuration in `backend/conftest.py`
- **Focus**: API endpoints, business logic, security validation

### Visual Testing
- Use Puppeteer MCP commands for UI validation
- Capture screenshots at 1440px viewport after frontend changes
- Verify responsive design across mobile/tablet/desktop
- Check console for JavaScript errors

## Workflow Guidelines

### Development Process
1. **Analysis**: Review existing code patterns and project structure
2. **Planning**: Break tasks into 3-7 logical steps
3. **Implementation**: Follow established patterns and naming conventions
4. **Testing**: Validate changes in isolation
5. **Documentation**: Update relevant docs and progress tracking

### WebSocket Communication
- Use `websocketService` for all WebSocket operations
- Implement robust connection management and error handling
- Use serialization-safe wrappers for data transmission

### Performance Optimization
- HTTP connection pooling for external services
- Resource monitoring and health checks
- Metrics collection and performance benchmarking

## File Organization

### Documentation
- `docs/CHANGELOG.md` - Track all changes
- `docs/STYLEGUIDE.md` - Frontend style guidelines
- `docs/SOLID.md` - Architecture principles
- Progress tracking in relevant sprint/task files

### Key Directories
- `frontend/components/` - Reusable UI components
- `backend/app/agents/` - Agent implementations
- `backend/app/api/` - API endpoints
- `backend/app/services/` - Business logic services

## Common Pitfalls to Avoid

- Code duplication - leverage existing utilities
- Expanding scope without approval
- Guessing requirements - always ask for clarification
- Skipping input validation or error handling
- Ignoring accessibility requirements
- Breaking existing component patterns

## Quality Gates

Before any commit:
- Lint and format code
- Run relevant tests
- Validate security patterns
- Check for circular dependencies
- Ensure proper error handling
- Update documentation as needed