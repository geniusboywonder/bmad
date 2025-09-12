### **SDLC_Process_Flow: Agent Orchestration Blueprint (Revised)**

This document outlines the sequential workflow for the BotArmy POC, from project initiation to completion. It defines the specific tasks, agent handoffs, and key Human-in-the-Loop (HITL) checkpoints. This serves as the blueprint for the Orchestrator, ensuring a consistent and predictable process for every project.

---

### **Phase 0: Discovery & Planning** 🗺️

**Objective:** Define the project scope and create a detailed plan to guide all subsequent phases, preventing misdirection and ensuring a shared understanding.

* **Task 0.1: Project Planning (Agent: Analyst)**
  * **Input:** User's initial high-level product idea.
  * **Process:** The Analyst agent interacts with the Context Store to generate a comprehensive project plan. This plan will outline the scope, the key milestones, the specific artifacts to be created, and the methodology for the requirements gathering.
  * **Output:** A `project_plan.json` artifact containing the proposed plan.
* **Task 0.2: HITL Checkpoint (Orchestrator)**
  * **Trigger:** Completion of the project planning.
  * **Action:** The Orchestrator creates a `HitlRequest` for the user to review and approve the project plan. This is a critical checkpoint to align on the scope before any work begins.
  * **Possible Outcomes:**
    * **Approve:** The workflow proceeds to Phase 1.
    * **Amend:** The Orchestrator provides the user's feedback to the Analyst agent, and the task is re-run with the new context.
    * **Reject:** The project is halted, and the user is notified.

---

### **Phase 1: Plan** 📝

**Objective:** Transform a high-level product idea into a detailed, actionable software specification.

* **Task 1.1: Requirements Analysis (Agent: Analyst)**
  * **Input:** User's initial product idea and the approved `project_plan.json` artifact.
  * **Process:** The Analyst agent interacts with the LLM and the Context Store to generate a list of functional requirements, non-functional requirements, and initial user stories.
  * **Output:** A `software_specification.json` artifact containing the refined requirements.
* **Task 1.2: HITL Checkpoint (Orchestrator)**
  * **Trigger:** Completion of the requirements analysis.
  * **Action:** The Orchestrator creates a `HitlRequest` for the user to review and approve the generated software specification.
  * **Possible Outcomes:**
    * **Approve:** The workflow proceeds to Phase 2.
    * **Amend:** The Orchestrator provides the user's feedback to the Analyst agent, and the task is re-run with the new context.
    * **Reject:** The project is halted, and the user is notified.

---

### **Phase 2: Design** 📐

**Objective:** Develop a technical architecture and implementation plan based on the approved specification.

* **Task 2.1: Architectural Design (Agent: Architect)**
  * **Input:** The approved `software_specification.json` artifact.
  * **Process:** The Architect agent designs the system architecture, defines the technology stack, and creates a high-level database schema.
  * **Output:** An `implementation_plan.json` artifact containing the architectural details.
* **Task 2.2: Implementation Planning (Agent: Architect)**
  * **Input:** The output from the previous task.
  * **Process:** The Architect breaks down the project into a list of specific, executable coding tasks for the Coder agent.
  * **Output:** An updated `implementation_plan.json` with a detailed task breakdown.

---

### **Phase 3: Build** 🏗️

**Objective:** Generate the initial proof-of-concept (POC) code based on the implementation plan.

* **Task 3.1: Code Generation (Agent: Coder)**
  * **Input:** The `implementation_plan.json` artifact.
  * **Process:** The Coder agent sequentially generates code for the defined components and functionality.
  * **Output:** A `source_code` artifact containing the generated code files.
* **Task 3.2: Code Refinement (Agent: Coder)**
  * **Input:** The initial `source_code` artifact.
  * **Process:** The Coder agent reviews and refines the generated code for quality, adherence to best practices, and integration with the overall architecture.
  * **Output:** An updated `source_code` artifact.

---

### **Phase 4: Validate** ✅

**Objective:** Test the generated code and ensure the POC is functional and meets the requirements.

* **Task 4.1: Code Testing (Agent: Tester)**
  * **Input:** The `source_code` artifact.
  * **Process:** The Tester agent analyzes the code and writes a set of unit tests and integration tests to validate its functionality.
  * **Output:** A `test_results.json` artifact with the test outcomes.
* **Task 4.2: Bug Fix (Agent: Coder)**
  * **Trigger:** A failure in the testing process.
  * **Process:** The Orchestrator provides the test results to the Coder agent for a bug-fix task.
  * **Output:** An updated `source_code` artifact with fixes. This is a loop that continues until tests pass.

---

### **Phase 5: Launch** 🚀

**Objective:** Deploy the functional POC to a live environment.

* **Task 5.1: Deployment (Agent: Deployer)**
  * **Input:** The validated `source_code` artifact and the `implementation_plan` (for environment details).
  * **Process:** The Deployer agent sets up the necessary infrastructure and deploys the application.
  * **Output:** A `deployment_log.json` artifact and a live URL for the deployed POC.
* **Task 5.2: Final Check (Agent: Deployer)**
  * **Input:** The live URL.
  * **Process:** The Deployer agent performs a final health check on the deployed application to confirm it is running as expected.
  * **Output:** The final `project_status` is updated to `completed`.
