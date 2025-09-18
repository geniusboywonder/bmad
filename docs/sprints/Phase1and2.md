# BotArmy Implementation Plan: Phase 1 & 2

## Overview

This document provides a comprehensive implementation plan for Phase 1 (Critical Foundation) and Phase 2 (Core Workflows) of the BotArmy multi-agent orchestration system. Frontend work is excluded from this plan and will be addressed separately.

**Timeline Estimate**: 4-6 weeks total
- **Phase 1**: 2-3 weeks (Critical Foundation)
- **Phase 2**: 2-3 weeks (Core Workflows)

---

# PHASE 1: CRITICAL FOUNDATION (2-3 weeks)

## P1.1 Database Setup with PostgreSQL + Redis (Week 1)

### P1.1.1 PostgreSQL Database Configuration
**Time Estimate**: 2-3 days

**Prerequisites:**
- PostgreSQL 14+ installed locally or accessible via Docker
- Database credentials configured in environment

**Tasks:**
1. **Database Connection Enhancement**
   - File: `backend/app/database/connection.py`
   - Implement connection pooling with SQLAlchemy
   - Add proper transaction management
   - Configure connection retry logic

2. **Alembic Migration Setup**
   - Initialize Alembic if not already done
   - Create initial migration from existing models in `backend/app/database/models.py`
   - Add database indexing for performance:
     - `projects.id`, `projects.created_at`
     - `tasks.project_id`, `tasks.agent_type`, `tasks.status`
     - `context_artifacts.project_id`, `context_artifacts.artifact_type`
     - `hitl_requests.project_id`, `hitl_requests.status`

3. **Environment Configuration**
   - Update `.env` with database URL
   - Add connection pool settings
   - Configure backup and recovery settings

**Validation Criteria:**
- [ ] Database tables created successfully
- [ ] Migrations run without errors
- [ ] Connection pooling working
- [ ] All indexes created and optimized

### P1.1.2 Redis Integration for Celery
**Time Estimate**: 1-2 days

**Tasks:**
1. **Redis Configuration**
   - Install and configure Redis server
   - Update `backend/app/tasks/celery_app.py` with Redis broker
   - Configure Redis for session management

2. **Celery Worker Setup**
   - Create worker process configuration
   - Implement task monitoring and retry logic
   - Add task result backend using Redis

3. **Queue Management**
   - Define separate queues for different agent types
   - Implement priority queue system
   - Add queue monitoring capabilities

**Files to Modify:**
- `backend/app/tasks/celery_app.py`
- `backend/app/tasks/agent_tasks.py`
- `backend/requirements.txt` (ensure Redis/Celery versions)

**Validation Criteria:**
- [ ] Celery workers start successfully
- [ ] Tasks can be queued and executed
- [ ] Redis monitoring shows proper queue usage
- [ ] Task retry logic works correctly

## P1.2 Multi-LLM Provider Configuration (Week 1-2)

### P1.2.1 LLM Provider Abstraction Layer
**Time Estimate**: 3-4 days

**Current State**: Only OpenAI integration exists
**Goal**: Support OpenAI, Anthropic Claude, Google Gemini

**Tasks:**
1. **Create Provider Interface**
   - New file: `backend/app/services/llm_providers/base_provider.py`
   - Define abstract base class for LLM providers
   - Standardize input/output formats across providers

2. **OpenAI Provider Implementation**
   - File: `backend/app/services/llm_providers/openai_provider.py`
   - Refactor existing OpenAI integration to use new interface
   - Add model-specific configurations

3. **Anthropic Claude Provider**
   - File: `backend/app/services/llm_providers/anthropic_provider.py`
   - Implement Claude API integration
   - Handle Claude-specific message formats
   - Add rate limiting and error handling

4. **Google Gemini Provider**
   - File: `backend/app/services/llm_providers/gemini_provider.py`
   - Implement Vertex AI/Gemini API integration
   - Handle Google-specific authentication

5. **Provider Factory and Configuration**
   - File: `backend/app/services/llm_providers/provider_factory.py`
   - Implement provider selection logic
   - Add environment-based provider configuration

**Dependencies to Add:**
```bash
# Add to requirements.txt
anthropic>=0.25.0
google-cloud-aiplatform>=1.60.0
google-generativeai>=0.8.0
```

**Configuration Schema:**
```python
# Environment variables needed
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_service_account.json

# Agent-to-LLM mapping
ANALYST_AGENT_PROVIDER=anthropic
ANALYST_AGENT_MODEL=claude-3-5-sonnet-20241022
ARCHITECT_AGENT_PROVIDER=openai
ARCHITECT_AGENT_MODEL=gpt-4o
CODER_AGENT_PROVIDER=openai
CODER_AGENT_MODEL=gpt-4o
TESTER_AGENT_PROVIDER=gemini
TESTER_AGENT_MODEL=gemini-1.5-pro
```

**Validation Criteria:**
- [ ] All three providers can be instantiated
- [ ] Each provider handles authentication correctly
- [ ] Provider selection works based on configuration
- [ ] Error handling works for API failures
- [ ] Cost tracking works across all providers

### P1.2.2 Agent-to-LLM Mapping System
**Time Estimate**: 2 days

**Tasks:**
1. **Configuration Service**
   - File: `backend/app/config/agent_configs.py`
   - Enhance to load provider mappings from environment
   - Add validation for provider/model combinations

2. **BaseAgent Integration**
   - File: `backend/app/agents/base_agent.py`
   - Update `_initialize_autogen_agent()` to use provider factory
   - Add provider-specific initialization logic

3. **Cost Tracking Updates**
   - File: `backend/app/services/llm_monitoring.py`
   - Update cost calculation for multiple providers
   - Add provider-specific pricing models

**Validation Criteria:**
- [ ] Each agent type uses configured LLM provider
- [ ] Cost tracking works for all providers
- [ ] Configuration validation prevents invalid combinations

## P1.3 AutoGen Conversation Patterns (Week 2)

### P1.3.1 Enhanced Agent Handoff System
**Time Estimate**: 3-4 days

**Current State**: Basic handoff schema exists
**Goal**: Full AutoGen conversation patterns with structured handoffs

**Tasks:**
1. **AutoGen Integration Enhancement**
   - File: `backend/app/services/autogen_service.py`
   - Implement AutoGen group chat capabilities
   - Add conversation state management
   - Create agent termination conditions

2. **Structured Handoff Implementation**
   - File: `backend/app/models/handoff.py`
   - Enhance HandoffSchema with AutoGen-compatible format
   - Add handoff validation and error handling
   - Implement context passing between agents

3. **Agent Communication Protocol**
   - File: `backend/app/agents/base_agent.py`
   - Update `create_handoff()` method for AutoGen compatibility
   - Add message validation and formatting
   - Implement conversation history tracking

4. **Group Chat Orchestration**
   - New file: `backend/app/services/group_chat_manager.py`
   - Implement AutoGen GroupChat for multi-agent scenarios
   - Add conflict resolution during conversations
   - Create conversation termination logic

**Key AutoGen Components to Implement:**
- GroupChat with custom speaker selection
- ConversableAgent with proper termination conditions
- Message validation and formatting
- Context preservation across agent switches

**Validation Criteria:**
- [ ] Agents can participate in group conversations
- [ ] Handoffs include complete context transfer
- [ ] Conversation state persists across sessions
- [ ] Termination conditions work correctly

### P1.3.2 Agent Team Configuration Loading
**Time Estimate**: 2 days

**Tasks:**
1. **BMAD Core Integration Preparation**
   - File: `backend/app/services/agent_team_service.py`
   - Enhance to load team configurations
   - Add team validation and error handling

2. **Configuration Schema**
   - Define agent team configuration format
   - Add team-specific LLM provider settings
   - Create team workflow definitions

**Validation Criteria:**
- [ ] Agent teams can be configured from files
- [ ] Team configurations validate correctly
- [ ] Teams can be dynamically assembled

## P1.4 BMAD Core Template Loading (Week 2-3)

### P1.4.1 Template System Implementation
**Time Estimate**: 3-4 days

**Current State**: Basic template service exists
**Goal**: Full YAML parsing with variable substitution

**Tasks:**
1. **Enhanced YAML Parser**
   - File: `backend/app/utils/yaml_parser.py`
   - Add Jinja2 template engine integration
   - Implement variable substitution
   - Add conditional logic support

2. **Template Service Enhancement**
   - File: `backend/app/services/template_service.py`
   - Implement dynamic template loading from `.bmad-core/`
   - Add template validation and caching
   - Create template inheritance system

3. **Workflow Definition Loading**
   - File: `backend/app/models/workflow.py`
   - Enhance to load from `.bmad-core/workflows/`
   - Add workflow validation
   - Implement workflow step definitions

4. **Template Categories Implementation**
   - Document templates (`.bmad-core/templates/`)
   - Workflow definitions (`.bmad-core/workflows/`)
   - Agent configurations (`.bmad-core/agent-teams/`)
   - Task definitions (`.bmad-core/tasks/`)

**Dependencies to Add:**
```bash
# Add to requirements.txt
jinja2>=3.1.0
pyyaml>=6.0
```

**Template Structure Example:**
```yaml
# .bmad-core/workflows/sdlc-workflow.yaml
name: "6-Phase SDLC Workflow"
version: "1.0"
phases:
  - name: "Discovery"
    agent: "analyst"
    template: "discovery-template.yaml"
    expected_outputs: ["project_plan", "user_requirements"]
  - name: "Plan"
    agent: "architect"
    template: "planning-template.yaml"
    dependencies: ["Discovery"]
    expected_outputs: ["technical_plan", "implementation_roadmap"]
```

**Validation Criteria:**
- [ ] Templates load from `.bmad-core/` directories
- [ ] Variable substitution works correctly
- [ ] Conditional logic evaluates properly
- [ ] Template validation catches errors
- [ ] Workflow definitions parse correctly

---

# PHASE 2: CORE WORKFLOWS (2-3 weeks)

## P2.1 6-Phase SDLC Orchestration (Week 3)

### P2.1.1 Orchestrator Enhancement
**Time Estimate**: 4-5 days

**Current State**: Basic orchestrator exists
**Goal**: Full 6-phase SDLC workflow management

**Tasks:**
1. **Workflow Engine Implementation**
   - File: `backend/app/services/workflow_engine.py`
   - Implement 6-phase workflow: Discovery → Plan → Design → Build → Validate → Launch
   - Add phase transition logic and validation
   - Create workflow state persistence

2. **Orchestrator Service Enhancement**
   - File: `backend/app/services/orchestrator.py`
   - Update to use workflow engine
   - Add time-conscious orchestration features
   - Implement front-loading of task details

3. **Workflow State Management**
   - File: `backend/app/models/workflow_state.py`
   - Enhance workflow state tracking
   - Add phase completion validation
   - Implement rollback capabilities

4. **Agent Coordination Logic**
   - File: `backend/app/agents/orchestrator.py`
   - Update to coordinate agent handoffs
   - Add conflict detection between agent outputs
   - Implement mediation logic

**6-Phase Workflow Implementation:**
```python
SDLC_PHASES = {
    "Discovery": {
        "agent": "analyst",
        "outputs": ["project_plan", "user_requirements", "success_criteria"],
        "templates": ["prd-template.yaml"],
        "validation": ["completeness_check", "clarity_validation"]
    },
    "Plan": {
        "agent": "analyst",
        "outputs": ["feature_breakdown", "acceptance_criteria"],
        "dependencies": ["Discovery"],
        "templates": ["planning-template.yaml"]
    },
    "Design": {
        "agent": "architect",
        "outputs": ["technical_architecture", "api_specifications", "data_models"],
        "dependencies": ["Plan"],
        "templates": ["architecture-template.yaml"]
    },
    "Build": {
        "agent": "coder",
        "outputs": ["source_code", "unit_tests", "documentation"],
        "dependencies": ["Design"],
        "templates": ["implementation-template.yaml"]
    },
    "Validate": {
        "agent": "tester",
        "outputs": ["test_results", "quality_report", "performance_metrics"],
        "dependencies": ["Build"],
        "templates": ["testing-template.yaml"]
    },
    "Launch": {
        "agent": "deployer",
        "outputs": ["deployment_log", "environment_config", "monitoring_setup"],
        "dependencies": ["Validate"],
        "templates": ["deployment-template.yaml"]
    }
}
```

**Validation Criteria:**
- [ ] All 6 phases execute in sequence
- [ ] Phase dependencies are validated
- [ ] Workflow state persists correctly
- [ ] Agent handoffs include complete context
- [ ] Rollback works for failed phases

### P2.1.2 Context Completeness System
**Time Estimate**: 2-3 days

**Tasks:**
1. **Context Injection Logic**
   - File: `backend/app/services/context_store.py`
   - Implement selective context injection for agents
   - Add context relevance scoring
   - Create context summarization for large artifacts

2. **Knowledge Artifact System**
   - Enhance context artifact creation
   - Add artifact relationship tracking
   - Implement artifact versioning

3. **Redundancy Prevention**
   - Add duplicate context detection
   - Implement context deduplication
   - Create context freshness validation

**Validation Criteria:**
- [ ] Agents receive relevant context only
- [ ] Context injection reduces redundant discovery
- [ ] Artifact relationships are tracked
- [ ] Context size is optimized for agent consumption

## P2.2 Agent-Specific Implementations (Week 3-4)

### P2.2.1 Analyst Agent Enhancement
**Time Estimate**: 3-4 days

**Current State**: Basic analyst agent exists
**Goal**: PRD generation with completeness validation

**Tasks:**
1. **PRD Generation Logic**
   - File: `backend/app/agents/analyst.py`
   - Implement structured PRD creation using BMAD templates
   - Add requirements completeness validation
   - Create user persona and business requirement generation

2. **Requirements Analysis Pipeline**
   - Add stakeholder interaction simulation
   - Implement missing requirement detection
   - Create clarifying question generation

3. **Success Criteria Definition**
   - Add acceptance criteria generation
   - Implement measurable goal creation
   - Create validation checkpoint definitions

**PRD Template Integration:**
```python
async def generate_prd(self, user_input: str, context: List[ContextArtifact]) -> Dict[str, Any]:
    """Generate Product Requirements Document using BMAD templates."""

    # Load PRD template from .bmad-core/templates/prd-template.yaml
    template = await self.template_service.load_template("prd-template.yaml")

    # Analyze user input for completeness
    analysis = await self._analyze_requirements_completeness(user_input)

    # Generate missing requirements if needed
    if not analysis.is_complete:
        missing_reqs = await self._generate_missing_requirements(analysis.gaps)
        # Create HITL request for clarification

    # Generate structured PRD
    prd_content = await self._generate_prd_content(template, user_input, context)

    return {
        "artifact_type": "project_plan",
        "content": prd_content,
        "completeness_score": analysis.completeness_score,
        "validation_status": "validated" if analysis.is_complete else "requires_input"
    }
```

**Validation Criteria:**
- [ ] PRDs include all required sections
- [ ] Completeness validation catches missing requirements
- [ ] HITL requests generated for clarification
- [ ] User personas and business requirements are comprehensive

### P2.2.2 Architect Agent Enhancement
**Time Estimate**: 3-4 days

**Tasks:**
1. **Technical Architecture Generation**
   - File: `backend/app/agents/architect.py`
   - Implement comprehensive technical architecture creation
   - Add API specification generation
   - Create data model definitions

2. **Implementation Planning**
   - Add detailed task breakdown creation
   - Implement dependency mapping
   - Create implementation timeline generation

3. **Risk Assessment Integration**
   - Add technical risk identification
   - Implement constraint analysis
   - Create mitigation strategy generation

**Architecture Template Integration:**
```python
async def create_technical_architecture(self, prd: ContextArtifact, context: List[ContextArtifact]) -> Dict[str, Any]:
    """Create comprehensive technical architecture from PRD."""

    # Load architecture template
    template = await self.template_service.load_template("architecture-template.yaml")

    # Analyze technical requirements from PRD
    tech_analysis = await self._analyze_technical_requirements(prd.content)

    # Generate system architecture
    architecture = await self._generate_system_architecture(tech_analysis, template)

    # Create API specifications
    api_specs = await self._generate_api_specifications(tech_analysis)

    # Generate implementation plan
    impl_plan = await self._create_implementation_plan(architecture, api_specs)

    return {
        "artifact_type": "software_specification",
        "content": {
            "architecture": architecture,
            "api_specifications": api_specs,
            "implementation_plan": impl_plan,
            "risk_assessment": await self._assess_technical_risks(architecture)
        }
    }
```

**Validation Criteria:**
- [ ] Technical architecture is comprehensive
- [ ] API specifications are complete and valid
- [ ] Implementation plans include realistic timelines
- [ ] Risk assessments identify major concerns
- [ ] Data models are properly normalized

### P2.2.3 Developer Agent (Coder) Enhancement
**Time Estimate**: 4-5 days

**Tasks:**
1. **Code Generation Pipeline**
   - File: `backend/app/agents/coder.py`
   - Implement production-ready code generation
   - Add code quality validation
   - Create comprehensive test generation

2. **Standards Compliance**
   - Add coding standards enforcement
   - Implement security best practices validation
   - Create performance optimization suggestions

3. **Documentation Generation**
   - Add inline code documentation
   - Create API documentation generation
   - Implement README and setup documentation

**Code Generation Template:**
```python
async def generate_implementation(self, architecture: ContextArtifact, context: List[ContextArtifact]) -> Dict[str, Any]:
    """Generate production-ready code from architecture specification."""

    # Load implementation template
    template = await self.template_service.load_template("implementation-template.yaml")

    # Parse architecture specifications
    arch_spec = architecture.content

    # Generate source code
    source_code = await self._generate_source_code(arch_spec, template)

    # Generate unit tests
    unit_tests = await self._generate_unit_tests(source_code)

    # Generate integration tests
    integration_tests = await self._generate_integration_tests(arch_spec)

    # Validate code quality
    quality_report = await self._validate_code_quality(source_code)

    return {
        "artifact_type": "source_code",
        "content": {
            "source_files": source_code,
            "unit_tests": unit_tests,
            "integration_tests": integration_tests,
            "documentation": await self._generate_documentation(source_code),
            "quality_metrics": quality_report
        }
    }
```

**Validation Criteria:**
- [ ] Generated code follows established patterns
- [ ] Unit tests achieve high coverage
- [ ] Code passes quality validation
- [ ] Documentation is comprehensive
- [ ] Security best practices are followed

### P2.2.4 Tester & Deployer Agent Enhancements
**Time Estimate**: 3-4 days total

**Tester Agent Tasks:**
1. **Test Plan Creation**
   - File: `backend/app/agents/tester.py`
   - Implement comprehensive test plan generation
   - Add edge case identification
   - Create performance test definitions

2. **Automated Testing Execution**
   - Add test execution simulation
   - Implement result analysis and reporting
   - Create defect classification and prioritization

**Deployer Agent Tasks:**
1. **Deployment Automation**
   - File: `backend/app/agents/deployer.py`
   - Implement deployment pipeline creation
   - Add environment configuration management
   - Create health check and monitoring setup

**Validation Criteria:**
- [ ] Test plans cover functional and edge cases
- [ ] Test execution provides detailed reports
- [ ] Deployment configurations are environment-specific
- [ ] Health checks validate system status

## P2.3 Enhanced HITL Triggers (Week 4)

### P2.3.1 Phase Completion Triggers
**Time Estimate**: 2-3 days

**Tasks:**
1. **Phase Gate Implementation**
   - File: `backend/app/services/hitl_trigger_manager.py`
   - Implement phase completion approval gates
   - Add phase transition validation
   - Create rollback mechanisms for rejected phases

2. **Confidence Threshold System**
   - Add agent confidence scoring
   - Implement automatic HITL trigger for low confidence
   - Create confidence improvement suggestions

3. **Quality Gate Integration**
   - Add quality metrics evaluation at each phase
   - Implement automatic quality gate failures
   - Create quality improvement recommendations

**Phase Gate Logic:**
```python
async def evaluate_phase_completion(self, phase: str, agent_output: Dict, project_id: UUID) -> bool:
    """Evaluate if phase completion requires HITL approval."""

    # Check confidence score
    confidence = agent_output.get("confidence_score", 0.0)
    if confidence < 0.8:
        await self._create_confidence_approval_request(phase, agent_output, project_id)
        return False

    # Check quality metrics
    quality_score = await self._evaluate_quality_metrics(agent_output)
    if quality_score < 0.85:
        await self._create_quality_approval_request(phase, agent_output, project_id)
        return False

    # Check phase-specific criteria
    phase_validation = await self._validate_phase_criteria(phase, agent_output)
    if not phase_validation.passed:
        await self._create_phase_approval_request(phase, agent_output, project_id)
        return False

    return True  # Auto-approve high-quality, high-confidence output
```

**Validation Criteria:**
- [ ] Phase gates trigger at appropriate thresholds
- [ ] Low confidence outputs require human review
- [ ] Quality gates prevent poor output progression
- [ ] Approval requests include sufficient context

### P2.3.2 Conflict Resolution Enhancement
**Time Estimate**: 2-3 days

**Tasks:**
1. **Conflict Detection System**
   - File: `backend/app/services/conflict_resolver.py`
   - Implement automated conflict detection between agent outputs
   - Add contradiction identification
   - Create conflict severity scoring

2. **Automated Mediation**
   - Add automated mediation attempts using project context
   - Implement constraint-based resolution
   - Create resolution confidence scoring

3. **Human Escalation**
   - Add structured conflict presentation for human review
   - Implement resolution tracking and learning
   - Create conflict prevention recommendations

**Conflict Resolution Pipeline:**
```python
async def resolve_agent_conflict(self, conflicts: List[AgentConflict], project_id: UUID) -> ResolutionResult:
    """Attempt automated conflict resolution with human escalation."""

    for attempt in range(3):  # Maximum 3 automated attempts
        # Try automated mediation
        resolution = await self._attempt_automated_mediation(conflicts, project_id)

        if resolution.success and resolution.confidence > 0.85:
            return resolution

        # Refine mediation approach
        conflicts = await self._refine_conflict_context(conflicts, resolution)

    # Escalate to human arbitration
    escalation = await self._create_human_arbitration_request(conflicts, project_id)
    return await self._wait_for_human_resolution(escalation)
```

**Validation Criteria:**
- [ ] Conflicts are detected automatically
- [ ] Automated mediation resolves simple conflicts
- [ ] Human escalation provides sufficient context
- [ ] Resolution tracking improves future mediation

## P2.4 Context Store Mixed-Granularity Enhancement (Week 4)

### P2.4.1 Intelligent Granularity System
**Time Estimate**: 3-4 days

**Tasks:**
1. **Granularity Analysis Engine**
   - File: `backend/app/services/artifact_service.py`
   - Implement artifact size analysis
   - Add complexity scoring for documents
   - Create optimal granularity recommendations

2. **Document Sectioning**
   - Add automatic document section detection
   - Implement section-level artifact creation
   - Create section relationship tracking

3. **Concept Extraction**
   - Add concept-level artifact extraction
   - Implement knowledge unit identification
   - Create concept relationship mapping

**Granularity Decision Logic:**
```python
async def determine_artifact_granularity(self, content: Dict, artifact_type: str) -> GranularityStrategy:
    """Determine optimal granularity for content storage."""

    content_size = self._calculate_content_size(content)
    complexity_score = await self._analyze_content_complexity(content)

    if content_size < 1000 and complexity_score < 0.3:
        return GranularityStrategy.ATOMIC  # Store as single artifact

    elif content_size > 5000 or complexity_score > 0.7:
        # Break into sections
        sections = await self._identify_logical_sections(content, artifact_type)
        return GranularityStrategy.SECTIONED(sections)

    else:
        # Store with concept extraction
        concepts = await self._extract_key_concepts(content)
        return GranularityStrategy.CONCEPTUAL(concepts)
```

**Validation Criteria:**
- [ ] Large documents are appropriately sectioned
- [ ] Small artifacts remain atomic
- [ ] Concept extraction identifies key knowledge units
- [ ] Granularity decisions improve agent efficiency

---

# TECHNICAL SPECIFICATIONS

## Development Environment Setup

### Prerequisites
```bash
# Backend Requirements
Python 3.11+
PostgreSQL 14+
Redis 6+
Docker (optional for databases)

# Required Python packages (see requirements.txt)
fastapi==0.104.1
sqlalchemy==2.0.43
celery==5.3.4
redis==5.0.1
autogen-agentchat==0.7.4
anthropic>=0.25.0
google-cloud-aiplatform>=1.60.0
jinja2>=3.1.0
pyyaml>=6.0
```

### Environment Configuration
```bash
# Database Configuration
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
REDIS_URL=redis://localhost:6379/0

# LLM Provider Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json

# Agent-to-LLM Mapping
ANALYST_AGENT_PROVIDER=anthropic
ANALYST_AGENT_MODEL=claude-3-5-sonnet-20241022
ARCHITECT_AGENT_PROVIDER=openai
ARCHITECT_AGENT_MODEL=gpt-4o
CODER_AGENT_PROVIDER=openai
CODER_AGENT_MODEL=gpt-4o
TESTER_AGENT_PROVIDER=gemini
TESTER_AGENT_MODEL=gemini-1.5-pro
DEPLOYER_AGENT_PROVIDER=openai
DEPLOYER_AGENT_MODEL=gpt-4o

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Database Schema Updates

### New Tables Required
```sql
-- LLM Provider Configuration
CREATE TABLE llm_provider_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL,
    provider_name VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    configuration JSON NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Execution State
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    workflow_template VARCHAR(100) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    phase_history JSON DEFAULT '[]',
    execution_context JSON DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent Conflict Resolution
CREATE TABLE agent_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    conflicting_agents JSON NOT NULL,
    conflict_description TEXT NOT NULL,
    resolution_attempts JSON DEFAULT '[]',
    resolution_status VARCHAR(50) DEFAULT 'pending',
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes to Add
```sql
-- Performance optimization indexes
CREATE INDEX idx_tasks_project_agent_status ON tasks(project_id, agent_type, status);
CREATE INDEX idx_context_artifacts_project_type ON context_artifacts(project_id, artifact_type);
CREATE INDEX idx_hitl_requests_project_status ON hitl_requests(project_id, status);
CREATE INDEX idx_workflow_executions_project_status ON workflow_executions(project_id, status);
```

## File Structure for New Components

```
backend/app/
├── services/
│   ├── llm_providers/
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   └── provider_factory.py
│   ├── workflow_engine.py
│   ├── conflict_resolver.py
│   ├── hitl_trigger_manager.py
│   └── group_chat_manager.py
├── agents/
│   ├── enhanced_analyst.py
│   ├── enhanced_architect.py
│   ├── enhanced_coder.py
│   ├── enhanced_tester.py
│   └── enhanced_deployer.py
└── templates/
    ├── workflow_templates/
    ├── agent_templates/
    └── document_templates/
```

## Testing Strategy

### Phase 1 Testing
- [ ] Database connection and migration tests
- [ ] LLM provider integration tests
- [ ] AutoGen conversation pattern tests
- [ ] Template loading and parsing tests

### Phase 2 Testing
- [ ] 6-phase workflow execution tests
- [ ] Agent-specific output validation tests
- [ ] HITL trigger condition tests
- [ ] Conflict resolution tests

### Integration Testing
- [ ] End-to-end workflow execution
- [ ] Multi-agent conversation scenarios
- [ ] Error recovery and rollback scenarios
- [ ] Performance under load testing

## Success Criteria

### Phase 1 Completion Criteria
- [ ] All three LLM providers (OpenAI, Anthropic, Gemini) working
- [ ] Database with proper indexing and migrations
- [ ] Redis-backed Celery task queue operational
- [ ] AutoGen conversation patterns implemented
- [ ] BMAD core template system loading dynamically
- [ ] Agent-to-LLM mapping configurable via environment

### Phase 2 Completion Criteria
- [ ] 6-phase SDLC workflow executing end-to-end
- [ ] All 5 agent types (Analyst, Architect, Coder, Tester, Deployer) enhanced
- [ ] HITL triggers working for phase completion and conflicts
- [ ] Context store supporting mixed-granularity artifacts
- [ ] Conflict resolution with automated mediation
- [ ] Comprehensive test coverage for all components

### Performance Targets
- [ ] API response times < 200ms for status queries
- [ ] Workflow phase transitions < 2 seconds
- [ ] Context artifact retrieval < 500ms
- [ ] HITL approval creation < 1 second
- [ ] Agent task initiation < 1 second

## Risk Mitigation

### Technical Risks
1. **LLM Provider API Limits**: Implement rate limiting and failover
2. **Database Performance**: Use connection pooling and proper indexing
3. **Memory Usage**: Implement artifact size limits and cleanup
4. **Workflow Complexity**: Start with simplified workflows, iterate

### Implementation Risks
1. **Scope Creep**: Stick to defined phase boundaries
2. **Integration Complexity**: Test components in isolation first
3. **Dependencies**: Have fallback plans for external service failures
4. **Time Estimation**: Build in 20% buffer for each phase

---

This implementation plan provides a systematic approach to building the critical foundation and core workflows for the BotArmy system. Each phase builds upon the previous one, ensuring a solid foundation for the advanced features.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create comprehensive Phase 1 & 2 implementation plan", "status": "completed", "activeForm": "Creating comprehensive Phase 1 & 2 implementation plan"}, {"content": "Define Phase 1 critical foundation tasks", "status": "completed", "activeForm": "Defining Phase 1 critical foundation tasks"}, {"content": "Define Phase 2 core workflow tasks", "status": "in_progress", "activeForm": "Defining Phase 2 core workflow tasks"}, {"content": "Include technical specifications and dependencies", "status": "pending", "activeForm": "Including technical specifications and dependencies"}, {"content": "Write implementation plan to docs/sprints/Phase1&2.md", "status": "pending", "activeForm": "Writing implementation plan to docs/sprints/Phase1&2.md"}]