// Initial demo data
const createDemoStages = (): ProcessStage[] => [
  // Requirements Stage
  {
    id: 'requirements',
    name: 'Requirements',
    description: 'Gather and analyze project requirements',
    status: 'done',
    agentName: 'Business Analyst',
    agentType: 'analyst',
    currentTask: 'Requirements analysis completed',
    hitlRequired: false,
    progress: 100,
    tasks: [
      {
        id: 'req-1',
        name: 'Gather initial requirements',
        status: 'done',
        assignedTo: 'Business Analyst',
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        completedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        progress: 100
      },
      {
        id: 'req-2',
        name: 'Create user stories',
        status: 'done',
        assignedTo: 'Business Analyst',
        createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        completedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        progress: 100
      },
      {
        id: 'req-3',
        name: 'Define acceptance criteria',
        status: 'done',
        assignedTo: 'Business Analyst',
        createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        completedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        progress: 100
      }
    ],
    artifacts: [
      {
        id: 'req-doc-1',
        name: 'Requirements Document',
        type: 'document',
        status: 'done',
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        createdBy: 'Business Analyst',
        downloadUrl: '/api/artifacts/req-doc-1'
      },
      {
        id: 'user-stories-1',
        name: 'User Stories',
        type: 'document',
        status: 'done',
        createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        createdBy: 'Business Analyst',
        downloadUrl: '/api/artifacts/user-stories-1'
      }
    ],
    startedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    estimatedDuration: 2 * 60 * 60 * 1000,
    nextStage: 'design'
  },

  // Design Stage  
  {
    id: 'design',
    name: 'Design',
    description: 'Create system architecture and design specifications',
    status: 'wip',
    agentName: 'System Architect',
    agentType: 'architect',
    currentTask: 'Creating database schema and API specifications',
    hitlRequired: true,
    progress: 65,
    tasks: [
      {
        id: 'design-1',
        name: 'Create system architecture',
        status: 'done',
        assignedTo: 'System Architect',
        createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        completedAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
        progress: 100
      },
      {
        id: 'design-2',
        name: 'Design database schema',
        status: 'wip',
        assignedTo: 'System Architect',
        createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
        progress: 80
      },
      {
        id: 'design-3',
        name: 'Create API specifications',
        status: 'todo',
        assignedTo: 'System Architect',
        createdAt: new Date().toISOString(),
        progress: 0
      }
    ],
    artifacts: [
      {
        id: 'arch-diagram-1',
        name: 'System Architecture Diagram',
        type: 'diagram',
        status: 'done',
        createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
        createdBy: 'System Architect',
        downloadUrl: '/api/artifacts/arch-diagram-1'
      }
    ],
    startedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    estimatedDuration: 3 * 60 * 60 * 1000,
    nextStage: 'development'
  },

  // Development Stage
  {
    id: 'development', 
    name: 'Development',
    description: 'Implement the solution based on design specifications',
    status: 'queued',
    agentName: 'Full Stack Developer',
    agentType: 'developer',
    currentTask: 'Waiting for design approval',
    hitlRequired: false,
    progress: 0,
    tasks: [
      {
        id: 'dev-1',
        name: 'Set up development environment',
        status: 'todo',
        assignedTo: 'Full Stack Developer',
        createdAt: new Date().toISOString(),
        progress: 0
      },
      {
        id: 'dev-2',
        name: 'Implement backend APIs',
        status: 'todo',
        assignedTo: 'Full Stack Developer',
        createdAt: new Date().toISOString(),
        progress: 0
      },
      {
        id: 'dev-3',
        name: 'Create frontend components',
        status: 'todo',
        assignedTo: 'Full Stack Developer',
        createdAt: new Date().toISOString(),
        progress: 0
      }
    ],
    artifacts: [],
    startedAt: undefined,
    estimatedDuration: 6 * 60 * 60 * 1000,
    nextStage: 'testing'
  },

  // Testing Stage
  {
    id: 'testing',
    name: 'Testing', 
    description: 'Validate solution quality and functionality',
    status: 'queued',
    agentName: 'QA Engineer',
    agentType: 'tester',
    currentTask: 'Waiting for development completion',
    hitlRequired: false,
    progress: 0,
    tasks: [
      {
        id: 'test-1',
        name: 'Create test plan',
        status: 'todo',
        assignedTo: 'QA Engineer', 
        createdAt: new Date().toISOString(),
        progress: 0
      },
      {
        id: 'test-2',
        name: 'Execute unit tests',
        status: 'todo',
        assignedTo: 'QA Engineer',
        createdAt: new Date().toISOString(),
        progress: 0
      },
      {
        id: 'test-3',
        name: 'Perform integration testing',
        status: 'todo',
        assignedTo: 'QA Engineer',
        createdAt: new Date().toISOString(),
        progress: 0
      }
    ],
    artifacts: [],
    startedAt: undefined,
    estimatedDuration: 4 * 60 * 60 * 1000,
    nextStage: 'deployment'
  },

  // Deployment Stage
  {
    id: 'deployment',
    name: 'Deployment',
    description: 'Deploy solution to production environment',
    status: 'queued', 
    agentName: 'DevOps Engineer',
    agentType: 'deployer',
    currentTask: 'Waiting for testing completion',
    hitlRequired: false,
    progress: 0,
    tasks: [
      {
        id: 'deploy-1',
        name: 'Prepare deployment environment',
        status: 'todo',
        assignedTo: 'DevOps Engineer',
        createdAt: new Date().toISOString(),
        progress: 0
      },
      {
        id: 'deploy-2', 
        name: 'Deploy to staging',
        status: 'todo',
        assignedTo: 'DevOps Engineer',
        createdAt: new Date().toISOString(),
        progress: 0
      },
      {
        id: 'deploy-3',
        name: 'Deploy to production',
        status: 'todo',
        assignedTo: 'DevOps Engineer',
        createdAt: new Date().toISOString(),
        progress: 0
      }
    ],
    artifacts: [],
    startedAt: undefined,
    estimatedDuration: 2 * 60 * 60 * 1000,
    nextStage: undefined
  }
]