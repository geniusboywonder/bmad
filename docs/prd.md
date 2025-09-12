# Product Requirements Document (PRD)

---

## 1. Introduction

### 1.1 Project Overview & Vision

BotArmy is an autonomous Product Generator that creates functional Proof-of-Concept (POC) web products. The system orchestrates multiple specialized agents through a sequential Software Development Lifecycle (SDLC). The core vision is to enable dynamic team assembly, multi-domain problem-solving, and seamless human-agent collaboration via a real-time interface.

### 1.2 Problem Statement

Traditional product development is slow and requires extensive manual coordination. BotArmy addresses this by streamlining the entire product creation process—from requirements gathering to deployment—through automated workflows, agent collaboration, and configurable human oversight.

---

## 2. Goals & Objectives

BotArmy aims to:

- **Automate Product Generation**: Create an end-to-end process for generating POC web products.
- **Enable Modular Agents**: Use specialized agents for each SDLC role (Analyst, Architect, Developer, Tester, Deployer).
- **Facilitate Seamless Interaction**: Ensure smooth communication and conflict resolution among agents with real-time monitoring.
- **Provide Configurable Human-in-the-Loop (HITL) Control**: Implement a mechanism for human Product Owner oversight, allowing control over the entire process, specific stages, or individual artifacts.
- **Maintain Transparency**: Deliver a full audit trail and transparent log of all agent interactions and decisions.

---

## 3. Target Audience

The stakeholders and users for the BotArmy platform include:

- **Human Product Owner**: Defines the initial vision and requirements and resolves conflicts.
- **Specialized AI Agents**: Includes Orchestrator, Analyst, Architect, Developer, Tester, and Deployer agents.
- **Human Orchestrator**: Oversees escalation and conflict resolution.

---

## 4. Scope

### 4.1 In-Scope

- **Product**: A functional Proof-of-Concept (POC) research platform.
- **Architecture**: Full-stack architecture with multi-LLM provider support, including OpenAI, Anthropic Claude, and Google Gemini. The frontend uses Next.js, React, and Tailwind CSS.
- **Deployment**: Initial deployment on GitHub Codespaces for rapid POC development, with a migration path to production platforms like Vercel.
- **Core Workflows**: The SDLC process from Analysis to Deployment, with a mandatory planning phase before each implementation.
- **Human Interaction**: An intuitive, real-time chat interface with a Human-in-the-Loop (HITL) system for approvals and conflict resolution.

### 4.2 Out-of-Scope (Future Considerations)

- Multi-tenancy and user authentication.
- Advanced analytics and monitoring dashboard.
- External tool integrations (e.g., GitHub, Slack, Jira, deployment platforms).
- Enterprise security and compliance.
- Artifact previews for images and PDFs.

---

## 5. Key Features & Functionality

BotArmy includes the following key features:

- Configurable HITL control for workflows, artifacts, and agent behavior.
- Multiple focused agents with specific briefs and skill sets.
- Live agent status indicators (Idle, Thinking, Waiting, Error).
- A central Orchestrator that directs and manages task completion, agent communication, and the overall workflow.
- An interactive SDLC process with status indicators (Plan, Queue, WIP, Done, HITL).
- Real-time event streaming to the UI to inform users of progress, artifact generation, or blockers.
- A user interface (UI) that provides:
  - A process overview with real-time status updates for phases, tasks, and artifacts.
  - The ability to download generated artifacts.
  - A chat interface for engaging with the Orchestrator and agents.
  - Environment and settings management.

### 5.1 Multi-Agent Orchestration

- **SDLC Workflow**: The Orchestrator manages five agents sequentially: Analyst, Architect, Developer, Tester, and Deployer.
- **Handoffs**: Agents exchange structured documents using a generic JSON schema applicable to various processes or product creation with different agents.
- **Real-Time Task Monitoring**: A real-time resource subscription model enables clients to subscribe to task state changes, supporting monitoring without polling.
- **Push Notifications**: The system sends push notifications for task completion to keep users informed.

### 5.2 Orchestrator Role

The Orchestrator serves as the central coordinator. It does not directly modify code but:

- **Analyzes** tasks and breaks them into focused subtasks.
- **Dispatches** Analyst agents to understand the system.
- **Delegates** implementation work to agents with precise instructions.
- **Verifies** changes through additional Analyst agents.
- **Maintains** the context store with all discovered knowledge.

#### 5.2.1 Time-Conscious Orchestration

The Orchestrator prioritizes time-efficient execution by addressing inefficiencies in task specification. This includes:

- **Front-Loading Details**: The Orchestrator crafts precise task descriptions to avoid iterative refinements.
- **Context Completeness**: It provides comprehensive context to prevent subagents from rediscovering known information.
- **Explicit Expectations**: Each task specifies expected outputs, eliminating unfocused exploration.
- **Tight Scoping**: Defines clear boundaries—what to do and what not to do—to prevent scope creep.

#### 5.2.2 Agent-as-Tools Architecture

The architecture enables the Orchestrator to coordinate a team of specialized agents in parallel, maintaining context and delivering coherent responses by treating subagents as tools for specific tasks.

### 5.3 Shared Context & Persistent Memory

The platform includes a persistent knowledge layer that transforms isolated agent actions into coherent problem-solving through the Context Store Pattern, which enables:

- **Orchestrator-Directed Discovery**: The Orchestrator specifies required contexts for each subagent, ensuring focused and relevant information gathering and implementation reporting.
- **Knowledge Artifacts**: Subagents create discrete, reusable context items based on the Orchestrator’s requirements.
- **Persistent Memory**: Contexts persist across agent interactions, building comprehensive system understanding.
- **Selective Injection**: The Orchestrator injects relevant contexts into new tasks, eliminating redundant discovery and providing all necessary information for subagents.
- **Compound Intelligence**: Each action builds on previous discoveries, creating exponential problem-solving capability.

### 5.4 Document Creation & Expert Roles

The system follows a structured process to ensure quality and user alignment in document creation:

- **1. Product Definition**  
  The Analyst guides the definition of product vision and requirements.  
  - **Required Topics**: Product Vision, User Personas, Business Requirements, Feature Map, and Success Criteria.  
  - **Output**: A comprehensive Product Requirements Document (PRD).

- **2. UX/UI Design & Technical Architecture**  
  The Architect defines the user experience and technical implementation plans.  
  - **Required Topics**: UI Documentation, Feature Specifications, User Journeys, Interaction Patterns, Data Requirements, Technical Architecture, API Specifications, Implementation Tasks, Database Schema, and Testing Strategy.  
  - **Output**: A comprehensive Software Specification.

- **3. User-Initiated Generation**  
  If the user requests document generation, the Orchestrator verifies that all required topics are covered. If any are missing, it continues the conversation until complete.

- **4. AI-Determined Readiness**  
  Each expert agent tracks topic completion and does not proceed to the next topic until the current one is sufficiently defined.

- **5. Mandatory User Verification**  
  Before concluding their stage, each expert agent (Analyst, Architect, etc.) verifies with the user that all requirements are accurately captured. The agent requests permission to generate the final document only after user approval.

- **6. Document Storage & Assembly**  
  Each expert’s document is saved individually. Upon completion of all stages, the Orchestrator generates a single, comprehensive document combining all agent outputs.

### 5.5 Stateful Process Management

The system implements stateful process management, where tasks persist to disk with atomic writes, ensuring durability and recovery.

### 5.6 Event-Driven Architecture

The platform operates using an event-driven architecture, where components emit events consumed by subsystems, including the Logger, State Manager, Notifier, and Metrics.

### 5.7 Human-in-the-Loop (HITL) System

- **Core Mechanism**: The system provides configurable HITL control, allowing users to set oversight levels for the entire process, specific stages, or individual artifacts.
- **Intelligent Routing**: A smart notification system offers one-click resolution for background tasks.
- **UI Integration**: HITL requests appear as inline approval interfaces in the chat and as badges in the process summary, with navigation to relevant context.
- **Conflict Resolution**: The system detects conflicts and escalates to the Human Product Owner with structured context after a maximum of three negotiation attempts.

---

## 6. Success Metrics

- **End-to-End Completion**: Achieve a complete end-to-end run of the process, producing all specified artifacts to a sufficient level of quality.
- **Reduced Manual Effort**: Reduce manual effort for complex workflows by 70-90%.

### **7. Functional Requirements (FRs)**

These requirements describe the specific features and functions the system must perform.

- **FR-01: Project Initiation:** The system must allow a user to initiate a new project by providing a high-level product idea via the chat interface.
- **FR-02: Agent Chat Interface:** The system must provide a real-time chat interface for the user to interact with the agents and see their responses.
- **FR-03: Multi-Agent Orchestration:** The system must orchestrate a sequence of specialized agents (Analyst, Architect, Coder, etc.) to progress a project from idea to a functional POC.
- **FR-04: Human-in-the-Loop (HITL):** The system must allow agents to pause and request clarification or approval from the human user before proceeding with a task.
- **FR-05: Real-time Status Updates:** The frontend must receive and display real-time status updates on the project's progress, including which agent is active and the current task.
- **FR-06: Task Status Tracking:** The system must track the status of each agent task (e.g., `idle`, `working`, `waiting_for_hitl`) and store it persistently.
- **FR-07: Context Persistence:** The system must store and retrieve all project-related information, including user inputs and agent outputs, in a persistent "Context Store."
- **FR-08: HITL Response Handling:** The system must process user responses to HITL requests, including **`approve`**, **`reject`**, and **`amend`** actions.
- **FR-09: Document Generation:** The system must generate and provide access to key project documents, such as the Software Specification and Implementation Plan.

***

### **8. Non-Functional Requirements (NFRs)**

These requirements specify criteria that can be used to judge the operation of the system, rather than specific behaviors.

- **NFR-01: Performance:** The real-time chat and status updates must have a latency of less than 500ms.
- **NFR-02: Scalability:** The system must be able to handle multiple simultaneous projects without a significant degradation in performance.
- **NFR-03: Reliability:** Agent tasks must be handled by a robust task queue system that can retry failed jobs and ensure no data is lost.
- **NFR-04: Maintainability:** The codebase must be modular and follow SOLID principles to allow for easy addition of new features and agents.
- **NFR-05: Security:** All API endpoints must be secure, and data must be protected from unauthorized access. The system must support authentication if user accounts are added in the future.
- **NFR-06: Monitoring:** The system must provide a health check endpoint to allow for automated monitoring and proactive issue detection.

***

### **9. Epics & Stories**

Here are some example Epics and user stories that can be used to plan the development sprints. An Epic is a large body of work, and a Story is a user-centric description of a feature.

#### **Epic 1: Project Lifecycle & Orchestration**

This epic covers the core workflow of a project, from initiation to completion.

- **Story: As a user, I want to start a new project by providing a product idea so that the agents can begin their work.** (Covers **FR-01**)
- **Story: As an Orchestrator, I need to manage the state of the project so that I can hand off tasks between agents.** (Covers **FR-03**)
- **Story: As a user, I want to see the real-time status of each agent so that I know what is happening with my project.** (Covers **FR-05**)

#### **Epic 2: Human-in-the-Loop (HITL) Interface**

This epic focuses on the interaction between the user and the agents.

- **Story: As a user, I want to be prompted for approval when an agent finishes a key planning task so that I can provide feedback.** (Covers **FR-04**)
- **Story: As a user, I want to amend an agent's response to a HITL request so that I can correct or refine their work.** (Covers **FR-08**)
- **Story: As a user, I want to see a history of all HITL requests and my responses so that I can review past decisions.**

#### **Epic 3: Data & State Management**

This epic ensures that all project information is handled correctly.

- **Story: As an agent, I need to read from the Context Store so that I can access previous outputs and artifacts.** (Covers **FR-07**)
- **Story: As an Orchestrator, I need to persist the state of all tasks so that the system can recover from a crash without losing progress.** (Covers **FR-06**)
- **Story: As a user, I want to be able to download the generated documentation so that I can share it with my team.** (Covers **FR-09**)
