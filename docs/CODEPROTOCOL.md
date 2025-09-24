# AGENT INSTRUCTIONS

**This protocol replaces all previous instructions and should be STRICTLY followed unless otherwise instructed BY THE USER**

## General Principles

- Always ask for clarification if uncertain about any aspect.
- Follow **all** provided instructions strictly unless explicitly stated otherwise.
- Edit only the minimum necessary code.
- Be succinct and avoid wasting tokens.
- ALWAYS follow the code protocol in `docs/CODEPROTOCOL.md`.
- ALWAYS follow the front-end style guide in `docs/STYLEGUIDE.md`.
- ALWAYS follow the SOLID principles in `docs/SOLID.md`.
- Use the README for project context.
- Document changes in `docs/CHANGELOG.md`.
- Document detailed, timestamped plans in `docs/PLAN.md`.
- Incrementally update `docs/PROGRESS.md`.
- Use a ToDo list for all planning and progress tracking.

## Development Commands

- Use provided npm and Python commands for frontend, backend, and full-stack development.
- Use Vitest for frontend testing and pytest for backend testing.

## Development Patterns

### Frontend

- Use functional components with hooks and proper TypeScript typings.
- Follow existing shadcn/ui component patterns and maintain import structure with `@/` paths.

### Backend

- Use FastAPI async patterns and Pydantic models for validation.
- Implement robust error handling.
- Use InputSanitizer for all user inputs and validate file uploads (size, type, content).
- Implement connection pooling for LLM providers and multi-level rate limiting.
- Detect and handle security patterns.

### Security

- Always sanitize inputs and validate with JSON Schema for YAML/configuration.
- Use secure wrappers to prevent circular references in serialization.
- Enforce multi-layer rate limiting (IP, user, global).
- Add security patterns detection and logging.
- Add tests for malicious input patterns.

## Code Standards

- Maximum 500 lines per file.
- Single responsibility for components and functions.
- Respect domain boundaries.
- Strict type safety; avoid any `any` types.
- Atomic and predictable state updates.
- Include error recovery mechanisms.
- Document performance considerations.
- Build accessibility in from the start.

### Service Architecture Standards

**Service Constructor Patterns**
- **String Paths Only**: Services must accept string paths, not dict configurations
  ```python
  # CORRECT
  service = MyService("config/path")

  # INCORRECT
  service = MyService({"path": "config/path"})
  ```

**SOLID Architecture Enforcement**
- **Maximum Service Size**: 600 LOC per service file
- **Single Responsibility**: Each service handles one domain concern
- **Interface Segregation**: All services must implement focused interfaces
- **Dependency Injection**: All services must use proper DI patterns for testability
- **Backward Compatibility**: Maintain service aliases during refactoring

**Configuration Management Standards**
- **Array vs String**: Configuration arrays use plural naming: `"items": ["name"]`
- **ID Validation**: All ID fields must use proper format validation (UUID, etc.)
- **Required Fields**: All schema objects must include all required fields
- **Type Consistency**: Maintain consistent data types across related configurations

### Database Integration Patterns

**Database Standards**
- **Real Database Required**: No mock-heavy database testing in integration tests
- **Session Management**: Use proper session managers for cleanup and isolation
- **Migration Validation**: All schema changes require migration testing
- **Connection Patterns**: Use connection pooling and proper session lifecycle management

### Import and Module Standards

**Import Path Standards**
- **Relative Imports**: Use proper relative imports within project structure
- **Module Resolution**: Validate import paths during development
- **Dependency Management**: Clearly separate internal vs external dependencies

## Testing Strategy

- Frontend: Vitest (unit tests), React Testing Library, global setup in `vitest.setup.ts`.
- Backend: pytest with async support (`pytest-asyncio`), configs in `backend/conftest.py`.

## Common Workflows

### Frontend Feature Development

- Create components per shadcn/ui patterns with TypeScript interfaces.
- Add client-side file upload validation.
- Test functionalities and security features.

### WebSocket Communication

- Use `websocketService` for all WebSocket operations.
- Manage connections and errors robustly.
- Use serialization-safe wrappers.
- Test with backend integration.

### Security Implementation

- Validate and sanitize inputs.
- Use JSON Schema validation.
- Implement rate limiting.
- Log security events.
- Add malicious input tests.
- Document security considerations.

### Performance Optimization

- Use HTTP connection pooling.
- Monitor metrics and provider health.
- Manage resources properly.
- Add performance and benchmarking tests.
- Optimize based on collected metrics.

### Workflow Stability

- Use parameter serialization: `persist_result=False`, `validate_parameters=False`.
- Prevent circular references with safe wrappers.
- Implement error recovery and cleanup.
- Add recursion prevention tests.
- Monitor workflow execution logs.

## Visual Development & Testing

### Quick Visual Check

- After any frontend change:
  - Identify changed components/pages.
  - Navigate to changed views using `mcp__puppeteer__puppeteer_navigate`.
  - Validate feature against requirements.
  - Capture full-page screenshots at desktop viewport (1440px).
  - Check console for errors using `mcp__puppeteer__puppeteer_evaluate`.

### Puppeteer MCP Commands

- Navigation, screenshots, interaction testing, and validation commands are available for UI testing.

### Design Compliance Checklist

- Verify visual hierarchy, consistency, responsiveness (mobile/tablet/desktop).
- Ensure accessibility (keyboard navigation, contrast, semantic HTML).
- Prioritize performance and error handling.
- Polish micro-interactions and loading states.

### Automated Visual Testing

- Use for any front-end changes or bug fixes.
- Skip for backend-only, config, documentation, tests, and non-visual utilities.

## Project and Code Management

- Break tasks into small, manageable steps.
- Always ask for clarifications before coding.
- Clearly state assumptions.
- Avoid code duplication by leveraging existing utilities.
- Use branching strategies for isolation.
- Regularly sync with the main branch.
- Archive old code rather than deleting.
- Enforce linting and formatting before commits.
- Commit after finishing features with clear messages.
- Document blockers and decisions in progress logs.
- Save work early if token limits are approached, with clear resume instructions.

## Coding Protocol

1. **Scan First**
   - Review README and project files carefully.
   - Never duplicate existing work.
   - Respect project patterns and naming.

2. **Plan & Track**
   - Update plans and progress files before coding.
   - Break work into 3-7 logical steps.
   - Avoid coding during planning (except lightweight scaffolding).
   - Seek clarifications first.
   - State assumptions.

3. **Code Standards**
   - Follow naming, structure, and dependencies.
   - Write modular, reusable, DRY code with error handling.
   - Test changes in isolation.
   - Follow style guide.

4. **Save & Document**
   - Isolate changes, use feature branches.
   - Sync frequently.
   - Archive older code.
   - Lint and format before commit.
   - Update documentation and progress.
   - Commit with clear messages.
   - Report untested code clearly.

## Production Readiness Criteria

### Code Quality Gates
- **Test Suite Health**: Minimum 95% test success rate required
- **Performance Standards**: API response times <200ms, real-time events <100ms
- **Architecture Compliance**: All services follow SOLID principles
- **Database Integration**: Real database testing for critical business logic
- **Error Handling**: Comprehensive error scenarios tested and documented

### Service Migration Standards
- **SOLID Refactoring**: Large services must be decomposed following SOLID principles
- **Interface First**: Create interfaces before implementing decomposed services
- **Backward Compatibility**: Maintain service aliases during migration periods
- **Test Coverage**: Maintain test coverage during service decomposition
- **Documentation**: Update architecture docs during major refactoring

## Systematic Debugging Protocol

### 🚨 PRIMARY DEBUGGING PRINCIPLES

**NEVER ASSUME - ALWAYS TRACE**
- Wrong: "Backend is working, frontend must be broken"
- Right: Trace every single step from user action to expected outcome
- Method: Start with the user action and follow the data through each system component

**START WITH THE SIMPLEST POSSIBLE TEST**
- Wrong: Test the entire complex workflow first
- Right: Can the user even trigger the initial action?
- Example: Before testing complex integrations, verify basic user actions work

**VERIFY EACH LINK IN THE CHAIN INDEPENDENTLY**
```
User Action → Frontend Processing → API Call → Backend Logic → Database → Queue → Response → UI Update
```
Test each arrow individually before testing the whole chain.

### 🔍 SYSTEMATIC DEBUGGING METHODOLOGY

**Step 1: Identify the Complete Data Flow**
- Map out every component the data must pass through
- Don't assume any component works - verify each one
- Document the expected data transformation at each step

**Step 2: Test the Happy Path First**
- Can the most basic version of the action happen?
- Only after basic flow works, add complexity

**Step 3: Use End-to-End Validation**
- After each "fix", test the complete user workflow
- Don't celebrate partial fixes - verify the end result
- Clear any mock data or cached state before testing

**Step 4: Trace Backwards from the Problem**
- Start with the user-visible symptom
- Work backwards: What should trigger this? Does that happen? What triggers that?
- Continue until you find the broken link

### ⚡ FAST DEBUGGING CHECKLIST

For any frontend-backend integration issue:

**Immediate Investigation (5 minutes)**
1. **Can the user action happen at all?** (Send message, click button, etc.)
2. **Does it reach the backend?** (Check network tab, backend logs)
3. **Does backend create expected data?** (Database queries, logs)
4. **Does backend broadcast events?** (WebSocket logs)
5. **Does frontend receive events?** (Browser console, WebSocket messages)
6. **Does frontend update state?** (Store inspection, React dev tools)
7. **Does UI reflect the state?** (Component re-rendering, conditional display)

**Root Cause Questions**
- **"What is the FIRST step that fails?"** - Don't assume early steps work
- **"Am I testing the real flow or mocked data?"** - Clear all caches first
- **"Does this fix directly address the user's symptom?"** - Avoid rabbit holes

### 🚫 DEBUGGING ANTI-PATTERNS TO AVOID

**1. Backend Obsession**
- Pattern: Fixing backend when frontend is the issue
- Solution: Listen to user feedback and focus on the actual problem area

**2. Premature Success Celebration**
- Pattern: Claiming success after partial fixes without end-to-end testing
- Solution: Only celebrate after complete user workflow is verified

**3. Irrelevant Bug Fixing**
- Pattern: Fixing unrelated issues while ignoring the main problem
- Solution: Always connect fixes directly to the end-user symptom

**4. Mock Data Confusion**
- Pattern: Testing with cached/persistent data and thinking it's real
- Solution: Always test in clean state - clear cache/localStorage first

### 📝 GENERIC DEBUGGING PROTOCOL

```
1. UNDERSTAND: What should happen end-to-end?
2. ISOLATE: What is the simplest test case?
3. TRACE: Follow data through each component
4. VERIFY: Test each component independently
5. VALIDATE: Confirm complete workflow works
6. DOCUMENT: Record the actual working flow
```

**Never skip step 3 (TRACE) - this is where most debugging failures happen.**

## Enforcement

- Stay in scope; don't expand tasks without approval.
- Never guess; ask questions.
- Fix errors immediately before proceeding.
- **Follow the systematic debugging protocol for all integration issues.**
