// Demo scenarios for testing the BotArmy system

export interface DemoScenario {
  title: string
  brief: string
  description: string
  estimatedTime: string
}

export const demoScenarios: DemoScenario[] = [
  {
    title: "Simple Todo App",
    brief: "Create a simple todo application with React frontend and Python FastAPI backend. Users should be able to add, edit, delete, and mark tasks as complete.",
    description: "A basic CRUD application perfect for testing the full agent workflow",
    estimatedTime: "5-10 minutes"
  },
  {
    title: "Blog Platform",
    brief: "Build a basic blog platform where users can create, read, update and delete blog posts. Include user authentication and a simple admin interface.",
    description: "More complex project involving authentication and admin features",
    estimatedTime: "10-15 minutes"
  },
  {
    title: "Weather Dashboard",
    brief: "Create a weather dashboard that displays current weather conditions and forecasts. Include location search and favorite locations feature.",
    description: "Integration with external APIs and data visualization",
    estimatedTime: "8-12 minutes"
  },
  {
    title: "Task Tracker",
    brief: "Develop a task tracking application for teams with project management features, user assignments, and progress tracking.",
    description: "Complex application with multiple user roles and project organization",
    estimatedTime: "15-20 minutes"
  },
  {
    title: "E-commerce Store",
    brief: "Build a simple e-commerce store with product catalog, shopping cart, and checkout process. Include basic inventory management.",
    description: "Full-featured application with complex business logic",
    estimatedTime: "20-25 minutes"
  },
  {
    title: "Chat Application",
    brief: "Create a real-time chat application with multiple rooms, user authentication, and message history.",
    description: "Real-time features testing WebSocket implementation",
    estimatedTime: "12-18 minutes"
  }
]

// Quick access to commonly used scenarios
export const defaultScenario = demoScenarios[0]
export const quickTestScenario = {
  title: "Quick Test",
  brief: "Create a simple Python Flask API that has one endpoint returning 'Hello, World!'",
  description: "Minimal test for quick agent workflow verification",
  estimatedTime: "2-3 minutes"
}