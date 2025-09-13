# Task 3: Integrate BMAD Core Template System with Backend

## Overview

Create the bridge between the BMAD Core template system and the Python backend, enabling dynamic workflow loading and template-driven document generation.

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1-2)

#### 1.1 YAML Parser Utilities

- **File**: `backend/app/utils/yaml_parser.py`
- **Purpose**: Robust YAML parsing with validation and error handling
- **Features**:
  - Schema validation for workflow and template files
  - Error handling with detailed error messages
  - Support for variable substitution placeholders
  - Type safety and validation

#### 1.2 Data Models

- **File**: `backend/app/models/workflow.py`
- **Purpose**: Pydantic models for workflow definitions
- **Features**:
  - Workflow metadata (id, name, description, type)
  - Agent sequence definitions
  - Handoff prompts and conditions
  - Mermaid diagram support

- **File**: `backend/app/models/template.py`
- **Purpose**: Pydantic models for document templates
- **Features**:
  - Template metadata and versioning
  - Section definitions with types
  - Variable substitution rules
  - Conditional logic support

### Phase 2: Template Service (Week 3-4)

#### 2.1 Template Service Implementation

- **File**: `backend/app/services/template_service.py`
- **Purpose**: Document generation with variable substitution
- **Features**:
  - Dynamic template loading from YAML files
  - Variable substitution engine
  - Conditional section rendering
  - Markdown output generation
  - Template validation and error handling

#### 2.2 Template Features

- Variable substitution: `{{variable_name}}`
- Conditional sections: `condition: variable_exists`
- List rendering: numbered and bulleted lists
- Table generation with dynamic columns
- Nested section support

### Phase 3: Workflow Service (Week 5-6)

#### 3.1 Workflow Service Implementation

- **File**: `backend/app/services/workflow_service.py`
- **Purpose**: Dynamic workflow execution and orchestration
- **Features**:
  - Workflow definition loading and parsing
  - Agent sequence management
  - Handoff prompt processing
  - Conditional workflow branching
  - Integration with agent framework

#### 3.2 Workflow Features

- Multi-agent sequence execution
- Conditional branching based on project type
- Handoff schema generation
- Progress tracking and state management
- Error handling and recovery

### Phase 4: Agent Team Configuration (Week 7-8)

#### 4.1 Agent Team Loader

- **File**: `backend/app/services/agent_team_service.py`
- **Purpose**: Load and manage agent team configurations
- **Features**:
  - Team composition loading from YAML
  - Agent role assignment and validation
  - Team-specific workflow adaptations
  - Configuration validation and error handling

### Phase 5: Integration Layer (Week 9-10)

#### 5.1 Agent Framework Integration

- **Update**: `backend/app/services/agent_service.py`
- **Purpose**: Integrate template system with agent framework
- **Features**:
  - Template-driven document generation for agents
  - Workflow-guided agent orchestration
  - Context artifact creation from templates
  - Handoff prompt processing

#### 5.2 API Endpoints

- **Update**: `backend/app/api/workflows.py` (new)
- **Purpose**: REST API for workflow management
- **Features**:
  - Workflow listing and selection
  - Template rendering endpoints
  - Agent team configuration APIs
  - Workflow execution status

### Phase 6: Testing & Validation (Week 11-12)

#### 6.1 Unit Tests

- **File**: `backend/tests/unit/test_template_service.py`
- **File**: `backend/tests/unit/test_workflow_service.py`
- **Coverage**: 95%+ for all new services
- **Features**: Comprehensive test coverage for all functionality

#### 6.2 Integration Tests

- **File**: `backend/tests/integration/test_template_integration.py`
- **File**: `backend/tests/integration/test_workflow_integration.py`
- **Coverage**: End-to-end workflow execution testing

#### 6.3 Validation Tests

- Template parsing and rendering validation
- Workflow execution with agent handoffs
- Error handling and edge cases
- Performance testing for large templates

## Technical Architecture

### Core Components

#### YAML Parser (`yaml_parser.py`)

```python
class YAMLParser:
    def load_workflow(self, file_path: str) -> WorkflowDefinition
    def load_template(self, file_path: str) -> TemplateDefinition
    def validate_schema(self, data: dict, schema: dict) -> bool
    def substitute_variables(self, template: str, variables: dict) -> str
```

#### Template Service (`template_service.py`)

```python
class TemplateService:
    def render_template(self, template_id: str, variables: dict) -> str
    def load_template(self, template_path: str) -> TemplateDefinition
    def validate_variables(self, template: TemplateDefinition, variables: dict) -> bool
    def process_conditionals(self, template: TemplateDefinition, context: dict) -> TemplateDefinition
```

#### Workflow Service (`workflow_service.py`)

```python
class WorkflowService:
    def load_workflow(self, workflow_id: str) -> WorkflowDefinition
    def execute_workflow(self, workflow: WorkflowDefinition, context: dict) -> WorkflowExecution
    def get_next_agent(self, workflow: WorkflowDefinition, current_step: int) -> AgentStep
    def generate_handoff(self, workflow: WorkflowDefinition, step: AgentStep) -> HandoffSchema
```

### Data Flow

1. **Workflow Loading**: YAML files loaded and parsed into Pydantic models
2. **Template Processing**: Variables substituted, conditionals evaluated
3. **Agent Orchestration**: Workflow steps executed with agent handoffs
4. **Document Generation**: Templates rendered to markdown output
5. **Context Integration**: Generated documents stored as context artifacts

### Integration Points

- **Agent Framework**: Template system provides document generation for agents
- **Context Store**: Generated documents stored as artifacts with metadata
- **WebSocket**: Real-time workflow progress updates
- **Database**: Workflow execution state and history persistence

## Success Criteria

- [ ] All BMAD Core workflows load and parse correctly
- [ ] Template system generates documents with proper variable substitution
- [ ] Agent team configurations integrate with agent framework
- [ ] Workflow service can execute complex multi-agent sequences
- [ ] Template validation prevents malformed configurations
- [ ] All tests pass with 95%+ coverage
- [ ] Performance meets requirements (< 200ms for template rendering)
- [ ] Error handling comprehensive and user-friendly

## Risk Mitigation

- **Schema Validation**: Strict validation prevents runtime errors
- **Error Recovery**: Graceful handling of malformed templates/workflows
- **Performance Monitoring**: Built-in metrics for optimization
- **Backward Compatibility**: Versioned templates support evolution
- **Testing Strategy**: Comprehensive test coverage for reliability

## Dependencies

- Task 2 (Agent Framework) - for agent integration
- Pydantic v2 - for data validation and serialization
- PyYAML - for YAML parsing
- Jinja2 - for template variable substitution

## Timeline

- **Week 1-2**: Core infrastructure and data models
- **Week 3-4**: Template service implementation
- **Week 5-6**: Workflow service implementation
- **Week 7-8**: Agent team configuration
- **Week 9-10**: Integration and API endpoints
- **Week 11-12**: Testing and validation

## Deliverables

1. YAML parser utilities with validation
2. Template service with variable substitution
3. Workflow service for orchestration
4. Agent team configuration loader
5. Integration with agent framework
6. Comprehensive test suite
7. API documentation and examples
