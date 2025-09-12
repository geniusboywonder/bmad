### **Frontend: Detailed Component & State Management Strategy**

This document provides a detailed breakdown of the frontend components and the state management strategy for the React/Next.js application, based on the provided UI screenshot and our architectural discussions. The design adheres to SOLID principles, ensuring the application is modular, maintainable, and scalable.

---

### **1. Component Breakdown**

The UI is decomposed into a hierarchy of reusable components, each with a single, well-defined responsibility (**SRP**).

#### **Top-Level Layout Components**

* **`AppLayout`**: The main container for the entire application. It defines the overall grid or flexbox layout and houses the primary sections.
* **`Sidebar`**: The vertical navigation bar on the left. It is responsible for navigation and displaying a set of fixed icons or links.
* **`MainContent`**: The central content area that contains the dashboard and the chat interface.

#### **Dashboard Components**

These components are responsible for displaying the overall project status and progress.

* **`ProcessSummary`**: A component that visualizes the project's progress through its lifecycle stages (`Plan`, `Design`, etc.) and shows the overall progress bar. It is a container for `StageIndicator` components.
  * **Sub-component**: `StageIndicator` - Displays a single stage icon, name, and status (e.g., active, complete).
* **`AgentStatusGrid`**: A container that displays the status of all available agents. It is composed of `AgentStatusCard` components.
  * **Sub-component**: `AgentStatusCard` - A small, reusable card for each agent, displaying its name and current status (`Idle`, `Working`). All `AgentStatusCard` instances will implement a common interface, demonstrating the **Liskov Substitution Principle (LSP)**.
* **`ArtifactSummary`**: A dynamic component that lists the project's key artifacts (e.g., `Execution Plan`, `User Stories`). It shows the completion status and is a container for `ArtifactItem` components.
  * **Sub-component**: `ArtifactItem` - A collapsible component for a single artifact, showing its title, progress, and download link.

#### **Chat Interface Components**

These components handle all user-agent communication within the chat window.

* **`ChatInterface`**: The main container for the chat. It is responsible for managing the display of messages and handling the real-time chat flow.
* **`MessageInput`**: The component at the bottom of the chat for user text input.
* **`ChatMessage`**: A single, reusable component for displaying a chat bubble. It will receive props for `sender` and `content`.
* **`HitlPrompt`**: A specialized component that renders a request for user input (e.g., "Please approve the plan..."), with buttons for `approve`, `reject`, and `amend`. This component demonstrates the **Open/Closed Principle (OCP)**, as it extends the core chat UI with new functionality without modifying the base chat component.

---

### **2. State Management Strategy**

We will use **Zustand** as the state management solution. It is a lightweight, hook-based library that is ideal for React and integrates seamlessly with Next.js. This approach aligns with the **Dependency Inversion Principle (DIP)** by making the components dependent on an abstraction (the Zustand store) rather than a concrete API client.

#### **Core Data Flow**

1. The frontend establishes a **WebSocket connection** to the backend's `/ws` endpoint.
2. Incoming real-time events from the WebSocket are listened to by a dedicated service or hook.
3. This service dispatches actions to the Zustand store, updating the state.
4. React components subscribed to the relevant parts of the state automatically re-render when changes occur.

#### **Zustand Store Slices**

The global state will be divided into "slices" to ensure each part of the state has a single responsibility (**SRP**).

* **`projectStore`**: Manages the overall project state.
  * `projectStatus`: String (`pending`, `active`, `completed`, `failed`).
  * `currentStage`: String (`plan`, `design`, etc.).
  * `currentTask`: Object with details about the active task.
* **`chatStore`**: Manages all chat messages.
  * `messages`: An array of message objects, each with `sender`, `type` (`text`, `hitl`), and `content`.
* **`agentStore`**: Tracks the real-time status of each agent.
  * `agents`: An object mapping agent types (e.g., `analyst`) to their status (`idle`, `working`).
* **`hitlStore`**: Manages all pending HITL requests.
  * `pendingRequests`: An array of `HitlRequest` objects.

#### **Implementation Details**

* **API Service**: A dedicated service will be created to handle the WebSocket connection and incoming event processing. This service will dispatch actions to the appropriate Zustand store slices.
* **Hooks**: We will create custom hooks (e.g., `useProjectStatus()`, `useChatMessages()`) to allow components to easily access and subscribe to the relevant state, adhering to the **Interface Segregation Principle (ISP)** by providing small, client-specific interfaces.
* **Immutability**: All state updates will be immutable, ensuring reliable change detection and preventing unexpected side effects.

This strategy provides a robust foundation for building a dynamic, real-time frontend that is easy to reason about and maintain.
